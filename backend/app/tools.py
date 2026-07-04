"""
All Shundo tools in one file: Calendar, Travel, Places, Web Search, Email,
Tasks, Notes, Budget, Weather, Currency, PDF parsing - plus the registry
that makes them all callable dynamically by name.
"""
import json
import time
import base64
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from pypdf import PdfReader

from app.auth import load_credentials
from app.config import TIMEZONE, SERPER_API_KEY
from app.db import get_connection
from app.llm import get_llm


# ============ CALENDAR ============

def _get_calendar_service(session_id: str = "default"):
    creds = load_credentials(session_id)
    if creds is None:
        return None  # caller decides how to handle "not connected" gracefully
    return build("calendar", "v3", credentials=creds)


def _to_local_iso(dt_str: str) -> str:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    return dt.isoformat()


def read_calendar_events(days_ahead: int = 14, session_id: str = "default") -> list[dict]:
    service = _get_calendar_service(session_id)
    if service is None:
        return []  # not connected yet - empty schedule, not an error

    now_local = datetime.now(ZoneInfo(TIMEZONE))
    later_local = now_local + timedelta(days=days_ahead)
    events_result = service.events().list(
        calendarId="primary", timeMin=now_local.isoformat(), timeMax=later_local.isoformat(),
        singleEvents=True, orderBy="startTime",
    ).execute()
    events = events_result.get("items", [])
    result = []
    for e in events:
        start_raw = e.get("start", {}).get("dateTime", e.get("start", {}).get("date"))
        end_raw = e.get("end", {}).get("dateTime", e.get("end", {}).get("date"))
        result.append({
            "id": e.get("id"), "title": e.get("summary", "(no title)"),
            "start": _to_local_iso(start_raw) if start_raw else None,
            "end": _to_local_iso(end_raw) if end_raw else None,
        })
    return result


def create_calendar_event(title: str, start_iso: str, end_iso: str, description: str = "", session_id: str = "default") -> dict:
    service = _get_calendar_service(session_id)
    if service is None:
        return {"error": "Not connected to Google Calendar yet. Sign in first to create real events."}

    start_clean = start_iso.replace("Z", "")
    end_clean = end_iso.replace("Z", "")
    event_body = {
        "summary": title, "description": description,
        "start": {"dateTime": start_clean, "timeZone": TIMEZONE},
        "end": {"dateTime": end_clean, "timeZone": TIMEZONE},
    }
    created = service.events().insert(calendarId="primary", body=event_body).execute()
    start_raw = created.get("start", {}).get("dateTime")
    end_raw = created.get("end", {}).get("dateTime")
    return {
        "id": created.get("id"), "title": created.get("summary"),
        "start": _to_local_iso(start_raw) if start_raw else None,
        "end": _to_local_iso(end_raw) if end_raw else None,
        "link": created.get("htmlLink"),
    }


def delete_calendar_event(event_id: str, session_id: str = "default") -> dict:
    service = _get_calendar_service(session_id)
    if service is None:
        return {"error": "Not connected to Google Calendar yet."}
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return {"deleted": True, "id": event_id}


# ============ TRAVEL (flights/hotels/events via Serper) ============

_SERPER_URL = "https://google.serper.dev/search"


def _serper_search(query: str, num_results: int = 4) -> list[dict]:
    response = requests.post(
        _SERPER_URL, headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
    )
    response.raise_for_status()
    data = response.json()
    return [
        {"title": i.get("title", ""), "snippet": i.get("snippet", ""), "link": i.get("link", "")}
        for i in data.get("organic", [])[:num_results]
    ]


def _extract_with_llm(raw_results: list[dict], extraction_prompt: str) -> list[dict]:
    if not raw_results:
        return []
    llm = get_llm(temperature=0.1)
    snippets_text = "\n\n".join(
        f"Title: {r['title']}\nSnippet: {r['snippet']}\nLink: {r['link']}" for r in raw_results
    )
    response = llm.invoke([
        {"role": "system", "content": extraction_prompt}, {"role": "user", "content": snippets_text},
    ])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def _sanity_filter_price(item: dict, min_price: int = 300) -> dict:
    """
    Cleans up misextracted prices - if price_estimate is a small number that's
    almost certainly a star rating or review count (not a real INR price),
    replace it with 'price on request' instead of showing a bogus number.
    """
    price = item.get("price_estimate")
    if isinstance(price, (int, float)) and price < min_price:
        item["price_estimate"] = "price on request"
    elif isinstance(price, str):
        digits = "".join(c for c in price if c.isdigit())
        if digits and int(digits) < min_price and "-" not in price and "to" not in price.lower():
            item["price_estimate"] = "price on request"
    return item


def search_flights(origin: str, destination: str, departure_date: str, adults: int = 1) -> list[dict]:
    query = f"flight price {origin} to {destination} {departure_date}"
    raw_results = _serper_search(query)
    prompt = """Extract REAL flight ticket prices from these search results. Respond ONLY with a JSON array, no other text.
Each item: {"airline": "...", "price_estimate": "...", "currency": "INR", "source": "..."}

CRITICAL: Only extract genuine ticket prices (typically 2000-25000 INR for domestic flights).
NEVER use star ratings, review counts, distances, or any other small number as a price.
If a result doesn't clearly state a fare price, skip it entirely rather than guessing.
Return an empty array [] if nothing usable is found."""
    results = _extract_with_llm(raw_results, prompt)
    return [_sanity_filter_price(r, min_price=800) for r in results]


def search_hotels(city: str, check_in: str, check_out: str, adults: int = 1) -> list[dict]:
    query = f"best hotels in {city} price per night booking"
    raw_results = _serper_search(query)
    prompt = """Extract REAL hotel prices per night from these search results. Respond ONLY with a JSON array, no other text.
Each item: {"name": "...", "price_estimate": "...", "currency": "INR", "source": "..."}

CRITICAL: Only extract genuine nightly room prices (typically 1000-20000 INR per night in India).
NEVER use star ratings (like "4.5"), review counts, number of rooms, or distances as a price.
Use "price on request" for price_estimate if no clear nightly price is stated, but still include
the hotel name if a real hotel name is present. Return an empty array [] only if no hotel names found."""
    results = _extract_with_llm(raw_results, prompt)
    return [_sanity_filter_price(r, min_price=800) for r in results]


def search_events(city: str, date: str = None) -> list[dict]:
    query = f"events in {city}" + (f" on {date}" if date else " this month")
    raw_results = _serper_search(query)
    prompt = """Extract event listings from these search results. Respond ONLY with a JSON array, no other text.
Each item: {"title": "...", "venue": "...", "date": "...", "source": "..."}
If information is missing, use "unknown" for that field. Return an empty array [] if nothing usable is found."""
    return _extract_with_llm(raw_results, prompt)


# ============ PLACES (OpenStreetMap - no key needed) ============

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
_OSM_HEADERS = {"User-Agent": "ShundoAgent/1.0 (hackathon project)"}


def _geocode(place_name: str):
    response = requests.get(_NOMINATIM_URL, params={"q": place_name, "format": "json", "limit": 1}, headers=_OSM_HEADERS)
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def search_places(location: str, category: str = "restaurant", radius_km: float = 3) -> list[dict]:
    coords = _geocode(location)
    if coords is None:
        return []
    lat, lon = coords
    radius_m = int(radius_km * 1000)
    tag_map = {
        "restaurant": 'node["amenity"="restaurant"]', "cafe": 'node["amenity"="cafe"]',
        "bar": 'node["amenity"="bar"]', "hotel": 'node["tourism"="hotel"]',
        "attraction": 'node["tourism"="attraction"]',
    }
    tag_query = tag_map.get(category, tag_map["restaurant"])
    overpass_query = f"[out:json][timeout:12];{tag_query}(around:{radius_m},{lat},{lon});out center 12;"

    data = None
    for url in _OVERPASS_URLS:
        try:
            response = requests.post(url, data={"data": overpass_query}, headers=_OSM_HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            break
        except Exception:
            continue

    if data is None:
        return []  # both mirrors failed - return empty rather than crashing the whole run

    results = []
    for el in data.get("elements", [])[:10]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        results.append({
            "name": name, "category": category, "address": tags.get("addr:street", ""),
            "lat": el.get("lat"), "lon": el.get("lon"), "cuisine": tags.get("cuisine", ""),
            "opening_hours": tags.get("opening_hours", ""),
        })
    return results


# ============ WEB SEARCH (generic) ============

def web_search(query: str, num_results: int = 5) -> list[dict]:
    response = requests.post(
        _SERPER_URL, headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
    )
    response.raise_for_status()
    data = response.json()
    results = [
        {"title": i.get("title", ""), "snippet": i.get("snippet", ""), "link": i.get("link", "")}
        for i in data.get("organic", [])[:num_results]
    ]
    answer_box = data.get("answerBox")
    if answer_box:
        results.insert(0, {"title": "Direct Answer", "snippet": answer_box.get("snippet") or answer_box.get("answer", ""), "link": answer_box.get("link", "")})
    return results


# ============ EMAIL DRAFT (Gmail) ============

def create_email_draft(to: str, subject: str, body: str, session_id: str = "default") -> dict:
    creds = load_credentials(session_id)
    if creds is None:
        return {"error": "Not connected to Gmail yet. Sign in first to create real drafts."}

    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw_message}}).execute()
    return {"draft_id": draft.get("id"), "to": to, "subject": subject, "status": "Draft created - review and send manually from Gmail."}


# ============ TASKS ============

def create_task(title: str, due_date: str = None, session_id: str = "default") -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (session_id, title, due_date) VALUES (?, ?, ?)", (session_id, title, due_date))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return {"id": task_id, "title": title, "due_date": due_date, "completed": False}


def list_tasks(include_completed: bool = False, session_id: str = "default") -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    if include_completed:
        cur.execute("SELECT * FROM tasks WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
    else:
        cur.execute("SELECT * FROM tasks WHERE session_id = ? AND completed = 0 ORDER BY created_at DESC", (session_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id: int, session_id: str = "default") -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = 1 WHERE id = ? AND session_id = ?", (task_id, session_id))
    conn.commit()
    conn.close()
    return {"id": task_id, "completed": True}


# ============ NOTES ============

def add_note(agent: str, content: str, session_id: str = "default") -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (session_id, agent, content) VALUES (?, ?, ?)", (session_id, agent, content))
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    return {"id": note_id, "agent": agent, "content": content}


def list_notes(limit: int = 20, session_id: str = "default") -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE session_id = ? ORDER BY created_at DESC LIMIT ?", (session_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============ BUDGET ============

def add_expense(category: str, amount, description: str = "", currency: str = "INR", session_id: str = "default") -> dict:
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return {"error": f"Invalid amount value: '{amount}' is not a real number. Expense was not logged."}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO budget_entries (session_id, category, description, amount, currency) VALUES (?, ?, ?, ?, ?)", (session_id, category, description, amount, currency))
    conn.commit()
    entry_id = cur.lastrowid
    conn.close()
    return {"id": entry_id, "category": category, "amount": amount, "currency": currency}


def get_total_spend(currency: str = "INR", session_id: str = "default") -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as total FROM budget_entries WHERE currency = ? AND session_id = ?", (currency, session_id))
    row = cur.fetchone()
    conn.close()
    return {"total": row["total"] or 0, "currency": currency}


def list_expenses(session_id: str = "default") -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM budget_entries WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============ WEATHER (Open-Meteo - no key needed) ============

def get_weather_forecast(city: str, date: str = None) -> dict:
    geo_response = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1})
    geo_response.raise_for_status()
    geo_data = geo_response.json()
    results = geo_data.get("results")
    if not results:
        return {"error": f"Could not find location: {city}"}
    lat, lon = results[0]["latitude"], results[0]["longitude"]
    forecast_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
            "timezone": "auto", "forecast_days": 16,
        },
    )
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json()
    daily = forecast_data.get("daily", {})
    dates = daily.get("time", [])
    if date and date in dates:
        idx = dates.index(date)
        return {"city": city, "date": date, "temp_max_c": daily["temperature_2m_max"][idx], "temp_min_c": daily["temperature_2m_min"][idx], "rain_chance_percent": daily["precipitation_probability_max"][idx]}
    if date:
        return {"error": f"No forecast available for {date} - Open-Meteo only forecasts up to 16 days ahead."}
    return {"city": city, "forecast": [
        {"date": dates[i], "temp_max_c": daily["temperature_2m_max"][i], "temp_min_c": daily["temperature_2m_min"][i], "rain_chance_percent": daily["precipitation_probability_max"][i]}
        for i in range(min(3, len(dates)))
    ]}


# ============ CURRENCY (open.er-api.com - no key needed) ============

def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    response = requests.get(f"https://open.er-api.com/v6/latest/{from_currency.upper()}")
    response.raise_for_status()
    data = response.json()
    rates = data.get("rates", {})
    to_code = to_currency.upper()
    if to_code not in rates:
        return {"error": f"Currency code not found: {to_code}"}
    rate = rates[to_code]
    return {"amount": amount, "from_currency": from_currency.upper(), "to_currency": to_code, "rate": rate, "converted_amount": round(amount * rate, 2)}


# ============ PDF PARSING ============

def parse_pdf(file_path: str) -> dict:
    reader = PdfReader(file_path)
    raw_text = ""
    for page in reader.pages:
        raw_text += page.extract_text() or ""
    if not raw_text.strip():
        return {"error": "No extractable text found in PDF (it may be a scanned image)."}
    raw_text = raw_text[:8000]
    llm = get_llm(temperature=0.1)
    prompt = """Extract structured information from this document. Respond ONLY with JSON, no other text.
Format: {"summary": "2-3 sentence summary", "important_dates": [{"date": "YYYY-MM-DD or as written", "description": "..."}], "tasks": ["actionable task 1", "..."]}
If no clear dates or tasks are found, return empty arrays for those fields."""
    response = llm.invoke([{"role": "system", "content": prompt}, {"role": "user", "content": raw_text}])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Could not parse structured data from document.", "raw_summary": raw[:500]}


# ============ REGISTRY (all tools, dynamically callable) ============

TOOL_SPECS = [
    {"name": "read_calendar_events", "description": "Read the user's real upcoming Google Calendar events to check for conflicts.", "function": read_calendar_events},
    {"name": "create_calendar_event", "description": "Create a real new event on the user's Google Calendar.", "function": create_calendar_event},
    {"name": "delete_calendar_event", "description": "Delete an event from the user's Google Calendar by ID.", "function": delete_calendar_event},
    {"name": "search_flights", "description": "Search the live web for real flight price information between two cities.", "function": search_flights},
    {"name": "search_hotels", "description": "Search the live web for real hotel price information in a city.", "function": search_hotels},
    {"name": "search_events", "description": "Search the live web for real local events in a city.", "function": search_events},
    {"name": "search_places", "description": "Find real restaurants, cafes, hotels, or attractions near a location.", "function": search_places},
    {"name": "web_search", "description": "Search the web for general information (visa rules, deadlines, facts, research).", "function": web_search},
    {"name": "create_email_draft", "description": "Create a real Gmail draft (does not auto-send) for the user to review.", "function": create_email_draft},
    {"name": "create_task", "description": "Create a new task or reminder.", "function": create_task},
    {"name": "list_tasks", "description": "List current tasks/reminders.", "function": list_tasks},
    {"name": "complete_task", "description": "Mark a task as completed.", "function": complete_task},
    {"name": "add_note", "description": "Log a note about what an agent did and why.", "function": add_note},
    {"name": "list_notes", "description": "Retrieve recent agent activity notes.", "function": list_notes},
    {"name": "add_expense", "description": "Log a planned or actual expense.", "function": add_expense},
    {"name": "get_total_spend", "description": "Get total spend so far.", "function": get_total_spend},
    {"name": "list_expenses", "description": "List all logged expenses.", "function": list_expenses},
    {"name": "get_weather_forecast", "description": "Get real weather forecast for a city, optionally for a specific date.", "function": get_weather_forecast},
    {"name": "convert_currency", "description": "Convert an amount between two currencies using real current exchange rates.", "function": convert_currency},
    {"name": "parse_pdf", "description": "Extract structured info (dates, tasks, summary) from an uploaded PDF document.", "function": parse_pdf},
]

TOOL_FUNCTIONS = {spec["name"]: spec["function"] for spec in TOOL_SPECS}
TOOL_DESCRIPTIONS = {spec["name"]: spec["description"] for spec in TOOL_SPECS}


def get_tools_catalog_text() -> str:
    import inspect
    lines = []
    for spec in TOOL_SPECS:
        sig = inspect.signature(spec["function"])
        params = ", ".join(str(p) for p in sig.parameters.values())
        lines.append(f"- {spec['name']}({params}): {spec['description']}")
    return "\n".join(lines)


def call_tool(name: str, arguments: dict):
    import inspect
    if name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {name}"}
    func = TOOL_FUNCTIONS[name]
    # Drop any argument names the function doesn't actually accept, instead
    # of crashing - handles minor naming drift from the LLM gracefully.
    valid_params = set(inspect.signature(func).parameters.keys())
    filtered_args = {k: v for k, v in arguments.items() if k in valid_params}
    try:
        return func(**filtered_args)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {str(e)}"}
