"""
Shundo backend - single entrypoint. Wires up Google OAuth, the calendar
reflection loop, the dynamic multi-tool loop, and test/cleanup routes.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_authorization_url, exchange_code_for_token, is_authenticated
from app.config import FRONTEND_ORIGIN
from app.tools import (
    read_calendar_events, create_calendar_event, delete_calendar_event,
    search_flights, search_hotels, search_events, search_places, web_search,
    create_email_draft, create_task, list_tasks, complete_task, add_note, list_notes,
    add_expense, get_total_spend, list_expenses, get_weather_forecast, convert_currency,
)
from app.agents import run_shundo, run_forced_conflict_test, run_dynamic_task, stream_dynamic_task

app = FastAPI(title="Shundo Backend")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Shundo backend is running"}


# --- Google OAuth ---

@app.get("/auth/google/login")
def google_login():
    return RedirectResponse(get_authorization_url())


@app.get("/auth/google/callback")
def google_callback(code: str):
    exchange_code_for_token(code)
    return JSONResponse({"status": "Google account connected successfully. You can close this tab."})


@app.get("/auth/google/status")
def google_status():
    return {"authenticated": is_authenticated()}


# --- Calendar reflection loop (proven demo centerpiece) ---

@app.get("/test/calendar/events")
def test_read_events():
    events = read_calendar_events()
    return {"count": len(events), "events": events}


@app.post("/test/calendar/create")
def test_create_event(title: str, start_iso: str, end_iso: str):
    return create_calendar_event(title, start_iso, end_iso)


@app.post("/agent/run")
def agent_run(goal: str):
    """Runs the calendar-specific planner->executor->critic reflection loop."""
    events = read_calendar_events()
    return run_shundo(goal, events)


@app.post("/test/agent/force-conflict")
def test_force_conflict(start_iso: str, end_iso: str):
    """Proves the reflection loop catches a real, deliberate conflict."""
    return run_forced_conflict_test(start_iso, end_iso)


# --- Dynamic multi-tool loop (domain-agnostic, any goal) ---

@app.post("/agent/dynamic")
def agent_dynamic(goal: str):
    """Runs the dynamic planner->executor->critic loop across ALL 11 tools."""
    return run_dynamic_task(goal)


@app.websocket("/ws/agent/dynamic")
async def ws_agent_dynamic(websocket: WebSocket):
    """
    WebSocket version: streams each trace step live as it happens instead
    of waiting for the whole run to finish. Frontend sends {"goal": "..."}
    once connected, then receives a stream of {"type": "step", "entry": {...}}
    messages, ending with {"type": "done", "result": {...full state...}}.
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        goal = data.get("goal", "")

        for message in stream_dynamic_task(goal):
            await websocket.send_json(message)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# --- Individual tool test routes ---

@app.get("/test/places")
def test_places():
    return search_places("Goa, India", category="restaurant")


@app.get("/test/travel/flights")
def test_flights():
    return search_flights("Delhi", "Goa", "2026-08-15")


@app.get("/test/travel/hotels")
def test_hotels():
    return search_hotels("Goa", "2026-08-15", "2026-08-18")


@app.get("/test/travel/events")
def test_events():
    return search_events("Goa")


@app.get("/test/websearch")
def test_websearch():
    return web_search("best time to visit Goa India")


@app.post("/test/email")
def test_email():
    return create_email_draft(to="test@example.com", subject="Test Draft from Shundo", body="This is a test draft.")


@app.get("/test/tasks")
def test_tasks():
    created = create_task("Pack bags for Goa trip", "2026-08-14")
    return {"created": created, "all_tasks": list_tasks()}


@app.get("/test/notes")
def test_notes():
    created = add_note("system", "Ran full system test")
    return {"created": created, "recent_notes": list_notes()}


@app.get("/test/budget")
def test_budget():
    entry = add_expense("flights", 6000, "Delhi to Goa flight")
    return {"entry": entry, "total_spend": get_total_spend()}


@app.get("/test/weather")
def test_weather():
    return get_weather_forecast("Goa")


@app.get("/test/currency")
def test_currency():
    return convert_currency(1000, "INR", "USD")


# --- Cleanup ---

@app.post("/cleanup/test-events")
def cleanup_test_events():
    """Deletes calendar events created during testing (safe - matches known test titles only)."""
    TEST_TITLES = {
        "Study Block", "Forced Conflict Test", "1 hour call",
        "Goa Road Trip", "Goa Roadtrip", "Goa Trip",
    }
    events = read_calendar_events(days_ahead=30)
    deleted = []
    for event in events:
        if event["title"] in TEST_TITLES:
            delete_calendar_event(event["id"])
            deleted.append(f"{event['title']} ({event['start']})")
    return {"deleted_count": len(deleted), "deleted_events": deleted}


# --- Budget API (real, used by the frontend Budget Tracker page) ---

class ExpenseIn(BaseModel):
    category: str
    amount: float
    description: str = ""
    currency: str = "INR"


@app.get("/api/budget")
def api_list_budget():
    return {"expenses": list_expenses(), "total": get_total_spend()}


@app.post("/api/budget")
def api_add_budget(expense: ExpenseIn):
    entry = add_expense(expense.category, expense.amount, expense.description, expense.currency)
    return {"entry": entry, "total": get_total_spend()}


# --- Tasks API (real, used by the frontend Tasks page) ---

class TaskIn(BaseModel):
    title: str
    due_date: str | None = None


@app.get("/api/tasks")
def api_list_tasks():
    return {"tasks": list_tasks(include_completed=True)}


@app.post("/api/tasks")
def api_add_task(task: TaskIn):
    return create_task(task.title, task.due_date)


@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: int):
    return complete_task(task_id)


# --- Calendar API (real, used by the frontend Calendar page) ---

@app.get("/api/calendar")
def api_calendar_events():
    events = read_calendar_events(days_ahead=30)
    return {"events": events, "authenticated": is_authenticated()}
