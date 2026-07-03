"""
All agent logic in one file: the calendar-specific reflection loop
(Planner -> Executor -> Critic, proven demo centerpiece) AND the dynamic
multi-tool loop (domain-agnostic, works for any goal using the full
tool registry). Both are LangGraph state machines, built from the
functions below.
"""
import json
from datetime import datetime
from typing import TypedDict, Optional
from zoneinfo import ZoneInfo

from langgraph.graph import StateGraph, END

from app.llm import get_llm
from app.config import TIMEZONE
from app.tools import read_calendar_events, create_calendar_event, get_tools_catalog_text, call_tool


# ============================================================
# CALENDAR-SPECIFIC REFLECTION LOOP (Planner -> Executor -> Critic)
# ============================================================

class ShundoState(TypedDict):
    goal: str
    calendar_events: list[dict]
    proposed_event: Optional[dict]
    created_event: Optional[dict]
    conflict: Optional[str]
    critic_summary: Optional[str]
    trace: list[dict]
    retry_count: int


PLANNER_SYSTEM_PROMPT = """You are the Planner in a scheduling agent.
Given the user's goal, the current local date/time, and their real upcoming
calendar events (all times shown are in the user's local timezone), propose
ONE new event to create.

If a conflict was found on a previous attempt, avoid that same time slot.

Respond ONLY with JSON in this exact shape, no other text, and give times as
naive local datetimes with NO timezone offset or "Z" suffix:
{"title": "...", "start_iso": "2026-07-10T14:00:00", "end_iso": "2026-07-10T16:00:00", "reasoning": "..."}
"""


def plan(state: ShundoState) -> dict:
    llm = get_llm(temperature=0.2)
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    context = f"""Current local date/time ({TIMEZONE}): {now_local.strftime('%Y-%m-%d %H:%M')} ({now_local.strftime('%A')})

User goal: {state['goal']}

Real upcoming calendar events (local time):
{json.dumps(state['calendar_events'], indent=2)}
"""
    if state.get("conflict"):
        context += f"\nPrevious attempt had a conflict: {state['conflict']}\nPropose a different time."

    response = llm.invoke([{"role": "system", "content": PLANNER_SYSTEM_PROMPT}, {"role": "user", "content": context}])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    proposed = json.loads(raw)

    trace_entry = {"agent": "planner", "action": "propose_event", "detail": proposed}
    return {"proposed_event": proposed, "trace": state["trace"] + [trace_entry]}


def execute(state: ShundoState) -> dict:
    proposed = state["proposed_event"]
    created = create_calendar_event(
        title=proposed["title"], start_iso=proposed["start_iso"], end_iso=proposed["end_iso"],
        description=proposed.get("reasoning", ""),
    )
    trace_entry = {"agent": "executor", "action": "create_calendar_event", "detail": created}
    return {"created_event": created, "trace": state["trace"] + [trace_entry]}


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def critique(state: ShundoState) -> dict:
    fresh_events = read_calendar_events()
    created = state["created_event"]
    is_retry = state["retry_count"] > 0

    created_start = datetime.fromisoformat(created["start"])
    created_end = datetime.fromisoformat(created["end"])
    conflict = None
    for event in fresh_events:
        if event["id"] == created["id"]:
            continue
        try:
            ev_start = datetime.fromisoformat(event["start"])
            ev_end = datetime.fromisoformat(event["end"])
        except (ValueError, TypeError):
            continue
        if _overlaps(created_start, created_end, ev_start, ev_end):
            conflict = f"Overlaps with '{event['title']}' ({event['start']} - {event['end']})"
            break

    if conflict:
        summary = (f"Still a conflict after rescheduling: {conflict}. Retrying with a new time." if is_retry
                    else f"Conflict detected: {conflict}. Rescheduling automatically.")
    else:
        summary = (f"Rescheduled successfully - '{created['title']}' now fits with no conflicts." if is_retry
                   else f"No conflicts found - '{created['title']}' is confirmed as scheduled.")

    trace_entry = {"agent": "critic", "action": "check_conflict", "detail": summary}
    return {
        "calendar_events": fresh_events, "conflict": conflict, "critic_summary": summary,
        "trace": state["trace"] + [trace_entry], "retry_count": state["retry_count"] + 1,
    }


def route_after_critic(state: ShundoState) -> str:
    if state["conflict"] and state["retry_count"] < 3:
        return "planner"
    return END


def build_calendar_graph():
    graph = StateGraph(ShundoState)
    graph.add_node("planner", plan)
    graph.add_node("executor", execute)
    graph.add_node("critic", critique)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "critic")
    graph.add_conditional_edges("critic", route_after_critic, {"planner": "planner", END: END})
    return graph.compile()


def run_shundo(goal: str, calendar_events: list[dict]) -> ShundoState:
    app_graph = build_calendar_graph()
    initial_state: ShundoState = {
        "goal": goal, "calendar_events": calendar_events, "proposed_event": None, "created_event": None,
        "conflict": None, "critic_summary": None, "trace": [], "retry_count": 0,
    }
    return app_graph.invoke(initial_state)


def run_forced_conflict_test(start_iso: str, end_iso: str) -> ShundoState:
    """Test-only: proves the reflection loop catches a real, deliberate conflict."""
    events = read_calendar_events()
    state: ShundoState = {
        "goal": "Schedule a study block (forced conflict test)", "calendar_events": events,
        "proposed_event": {
            "title": "Forced Conflict Test", "start_iso": start_iso, "end_iso": end_iso,
            "reasoning": "Deliberately picked a known-busy slot to test the reflection loop.",
        },
        "created_event": None, "conflict": None, "critic_summary": None, "trace": [], "retry_count": 0,
    }
    state.update(execute(state))
    state.update(critique(state))
    while state["conflict"] and state["retry_count"] < 3:
        state.update(plan(state))
        state.update(execute(state))
        state.update(critique(state))
    return state


# ============================================================
# DYNAMIC MULTI-TOOL LOOP (domain-agnostic, any goal, any tools)
# ============================================================

class DynamicState(TypedDict):
    goal: str
    tool_calls: list[dict]
    tool_results: list[dict]
    critic_summary: Optional[str]
    trace: list[dict]
    retry_count: int
    needs_retry: bool


def plan_dynamic(state: DynamicState) -> dict:
    llm = get_llm(temperature=0.2)
    catalog = get_tools_catalog_text()
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    system_prompt = f"""You are the Planner in a multi-tool agent. Given the user's goal, decide which
tool(s) from the catalog below to call, in order, and with what arguments.

CRITICAL: Today's real date is {now_local.strftime('%Y-%m-%d')} ({now_local.strftime('%A')}). You MUST
use this as your reference point for any relative date in the goal. NEVER output a year earlier than
{now_local.year}. All dates you generate must be {now_local.strftime('%Y-%m-%d')} or later.

Available tools (use these EXACT argument names, shown in parentheses):
{catalog}

Respond ONLY with a JSON array, no other text. Each item:
{{"tool": "tool_name", "args": {{"arg1": "value1"}}}}

Use only the EXACT argument names shown in the tool signatures above - do not invent alternate names.
Call only the tools genuinely needed for this goal."""

    context = f"User goal: {state['goal']}"
    if state.get("critic_summary"):
        context += f"\n\nPrevious attempt feedback: {state['critic_summary']}\nAdjust your plan accordingly."

    response = llm.invoke([{"role": "system", "content": system_prompt}, {"role": "user", "content": context}])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        tool_calls = json.loads(raw)
    except json.JSONDecodeError:
        tool_calls = []

    trace_entry = {"agent": "planner", "action": "select_tools", "detail": tool_calls}
    return {"tool_calls": tool_calls, "trace": state["trace"] + [trace_entry]}


def execute_dynamic(state: DynamicState) -> dict:
    from concurrent.futures import ThreadPoolExecutor

    calls = state["tool_calls"]

    def run_one(c):
        tool_name = c.get("tool")
        args = c.get("args", {})
        result = call_tool(tool_name, args)
        return {"tool": tool_name, "args": args, "result": result}

    with ThreadPoolExecutor(max_workers=max(len(calls), 1)) as pool:
        results = list(pool.map(run_one, calls))

    trace_additions = [
        {"agent": "executor", "action": f"call_{r['tool']}", "detail": r["result"]} for r in results
    ]
    return {"tool_results": results, "trace": state["trace"] + trace_additions}


def critique_dynamic(state: DynamicState) -> dict:
    results = state["tool_results"]
    has_errors = any(isinstance(r.get("result"), dict) and "error" in r.get("result", {}) for r in results)

    if not results:
        summary, needs_retry = "No tools were called - nothing to review.", True
    elif has_errors:
        errors = [r for r in results if isinstance(r.get("result"), dict) and "error" in r.get("result", {})]
        summary = f"Some tool calls failed: {errors}. May need different arguments."
        needs_retry = state["retry_count"] < 2
    else:
        # Deterministic summary (no extra LLM call) - much faster, still informative
        tool_names = ", ".join(sorted(set(r["tool"] for r in results)))
        summary = f"Completed successfully using: {tool_names}. {len(results)} tool call(s) returned real data."
        needs_retry = False

    trace_entry = {"agent": "critic", "action": "review_results", "detail": summary}
    return {
        "critic_summary": summary, "trace": state["trace"] + [trace_entry],
        "retry_count": state["retry_count"] + 1, "needs_retry": needs_retry,
    }


def route_after_dynamic_critic(state: DynamicState) -> str:
    if state.get("needs_retry") and state["retry_count"] <= 2:
        return "planner"
    return END


def build_dynamic_graph():
    graph = StateGraph(DynamicState)
    graph.add_node("planner", plan_dynamic)
    graph.add_node("executor", execute_dynamic)
    graph.add_node("critic", critique_dynamic)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "critic")
    graph.add_conditional_edges("critic", route_after_dynamic_critic, {"planner": "planner", END: END})
    return graph.compile()


def run_dynamic_task(goal: str) -> DynamicState:
    app_graph = build_dynamic_graph()
    initial_state: DynamicState = {
        "goal": goal, "tool_calls": [], "tool_results": [], "critic_summary": None,
        "trace": [], "retry_count": 0, "needs_retry": False,
    }
    return app_graph.invoke(initial_state)


def stream_dynamic_task(goal: str):
    """
    Generator version for WebSocket streaming: yields only the NEW trace
    entries after each graph step, instead of waiting for the whole run
    to finish. Used by the /ws/agent/dynamic WebSocket route.
    """
    app_graph = build_dynamic_graph()
    initial_state: DynamicState = {
        "goal": goal, "tool_calls": [], "tool_results": [], "critic_summary": None,
        "trace": [], "retry_count": 0, "needs_retry": False,
    }

    seen_count = 0
    final_state = None

    for state_update in app_graph.stream(initial_state, stream_mode="values"):
        final_state = state_update
        trace = state_update.get("trace", [])
        new_entries = trace[seen_count:]
        for entry in new_entries:
            yield {"type": "step", "entry": entry}
        seen_count = len(trace)

    yield {"type": "done", "result": final_state}
