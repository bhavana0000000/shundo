"""
Shundo backend - single entrypoint. Wires up Google OAuth, the calendar
reflection loop, the dynamic multi-tool loop, and test/cleanup routes.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Response, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
import os
import tempfile
from collections import defaultdict

from app.config import FRONTEND_ORIGIN
from app.auth import get_authorization_url, exchange_code_for_token, is_authenticated, get_user_info
from app.tools import (
    read_calendar_events, create_calendar_event, delete_calendar_event,
    search_flights, search_hotels, search_events, search_places, web_search,
    create_email_draft, create_task, list_tasks, complete_task, add_note, list_notes,
    add_expense, get_total_spend, list_expenses, get_weather_forecast, convert_currency,
    parse_pdf,
)
from app.agents import run_shundo, run_forced_conflict_test, run_dynamic_task, stream_dynamic_task

app = FastAPI(title="Shundo Backend")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


# --- Session identity (per-browser data isolation for tasks/budget/notes) ---
# IMPORTANT: We no longer rely on cookies for this. Cross-domain cookies
# (frontend on pages.dev, backend on onrender.com) get silently blocked or
# expired by modern browsers (Safari ITP, Chrome privacy protections) -
# that's what was causing sign-in to randomly reset to guest mode. Instead,
# the frontend generates its own session ID (stored in localStorage) and
# sends it as a header on fetch requests, or a query param on the
# WebSocket/OAuth-redirect URLs (which can't carry custom headers).

SESSION_HEADER_NAME = "x-shundo-session"


def get_or_create_session_id(request: Request, response: Response = None) -> str:
    """Reads the session ID from the request header (sent by the frontend).
    Falls back to a fresh one only if the frontend genuinely sent nothing -
    this should be rare once the frontend is updated."""
    session_id = request.headers.get(SESSION_HEADER_NAME)
    if not session_id:
        session_id = request.query_params.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id


def get_session_id_from_ws(websocket: WebSocket) -> str:
    """WebSocket version - reads session_id from the query string, since
    browsers can't attach custom headers to a WebSocket handshake."""
    return websocket.query_params.get("session_id") or str(uuid.uuid4())


# --- Rate limiting (protects LLM quota from abuse by public visitors) ---
# Simple in-memory sliding window: N requests per IP per time window.
# Good enough for a demo - resets when the server restarts, no external
# dependency needed (Redis etc would be needed for a real multi-instance setup).

_rate_limit_store = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 15
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour


def check_rate_limit(key: str):
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]

    if len(_rate_limit_store[key]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit reached ({RATE_LIMIT_MAX_REQUESTS} runs/hour on this demo). Try again later.",
        )
    _rate_limit_store[key].append(now)


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "Shundo backend is running"}


# --- Google OAuth ---

@app.get("/auth/google/login")
def google_login(request: Request):
    session_id = get_or_create_session_id(request)  # frontend passes ?session_id=... on this URL
    auth_url = get_authorization_url(session_id)
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback")
def google_callback(code: str, state: str):
    # 'state' carries the session_id through Google's redirect round-trip
    exchange_code_for_token(code, session_id=state)
    # Send the user back into the real app instead of leaving them on a bare backend JSON page
    return RedirectResponse(f"{FRONTEND_ORIGIN}/app")


@app.get("/auth/google/status")
def google_status(request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    authenticated = is_authenticated(session_id)
    user_info = get_user_info(session_id) if authenticated else None
    return {"authenticated": authenticated, "user": user_info}


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
def agent_dynamic(goal: str, request: Request, response: Response):
    """Runs the dynamic planner->executor->critic loop across ALL 11 tools."""
    session_id = get_or_create_session_id(request, response)
    check_rate_limit(session_id)
    return run_dynamic_task(goal, session_id=session_id)


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
        session_id = get_session_id_from_ws(websocket)
        check_rate_limit(session_id)

        data = await websocket.receive_json()
        goal = data.get("goal", "")

        for message in stream_dynamic_task(goal, session_id=session_id):
            await websocket.send_json(message)

    except HTTPException as e:
        await websocket.send_json({"type": "error", "message": e.detail})
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
def api_list_budget(request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    return {"expenses": list_expenses(session_id=session_id), "total": get_total_spend(session_id=session_id)}


@app.post("/api/budget")
def api_add_budget(expense: ExpenseIn, request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    entry = add_expense(expense.category, expense.amount, expense.description, expense.currency, session_id=session_id)
    return {"entry": entry, "total": get_total_spend(session_id=session_id)}


# --- Tasks API (real, used by the frontend Tasks page) ---

class TaskIn(BaseModel):
    title: str
    due_date: str | None = None


@app.get("/api/tasks")
def api_list_tasks(request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    return {"tasks": list_tasks(include_completed=True, session_id=session_id)}


@app.post("/api/tasks")
def api_add_task(task: TaskIn, request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    return create_task(task.title, task.due_date, session_id=session_id)


@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: int, request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    return complete_task(task_id, session_id=session_id)


# --- Calendar API (real, used by the frontend Calendar page) ---

@app.get("/api/calendar")
def api_calendar_events(request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    events = read_calendar_events(days_ahead=30, session_id=session_id)
    return {"events": events, "authenticated": is_authenticated(session_id)}


# --- PDF upload API (real, used by the frontend document upload feature) ---

@app.post("/api/upload-pdf")
async def api_upload_pdf(file: UploadFile = File(...)):
    """Accepts a real PDF upload, extracts structured info (dates, tasks,
    summary) using the same parse_pdf tool the agent can call itself."""
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Please upload a PDF file."}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = parse_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)  # always clean up the temp file, even on error

    return result
