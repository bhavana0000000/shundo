# Shundo

**An autonomous AI agent that turns a vague goal into real, executed actions.**

🔗 **Live demo:** [shundo.pages.dev](https://shundo.pages.dev)

---

## What it is

Shundo is a domain-agnostic "chief of staff" agent. Give it a goal — "plan a weekend trip to Goa," "schedule a study block this week," "plan the best way to learn DSA" — and it doesn't reply with a text plan you still have to execute yourself. It reasons through the goal, decides which real tools it needs, calls them for real against live services, checks its own work against fresh data, and fixes its own mistakes before it finishes.

The name comes from the Japanese word **旬 (shun)** — the moment something is at its peak, ready, in season. Shundo finds the right moment and the right action for any goal, and acts on it.

---

## How it works — a real reflection loop, not a single LLM call

Shundo runs on a three-agent graph, built with **LangGraph**:

- **Planner** — reads the goal and the full tool registry, then decides which tools to call and with what arguments. Nothing is hardcoded per domain.
- **Executor** — calls the tools the planner selected, for real, against real APIs. Calls run in parallel where possible.
- **Critic** — reviews what the executor actually did against **fresh, re-fetched real data**. If something's wrong — a scheduling conflict, a failed tool call — it routes back to the Planner with the specific problem, and the loop runs again.

This loop is provably real: in testing, the Critic caught an actual double-booked calendar slot, described the conflict back to the Planner, and the Planner proposed a different time — verified against a real Google Calendar, not mocked data.

The entire trace streams live to the frontend over a WebSocket, so you watch the agent think step by step instead of waiting for a spinner.

---

## The 11 tools

| Tool | What it does | Data source |
|---|---|---|
| **Calendar** | Reads and writes real Google Calendar events, per logged-in user | Google Calendar API (OAuth) |
| **Email drafts** | Creates real Gmail drafts (never auto-sends) | Gmail API (OAuth) |
| **Flights** | Live flight price search | Serper.dev + LLM extraction |
| **Hotels** | Live hotel price search | Serper.dev + LLM extraction |
| **Events** | Local event search | Serper.dev + LLM extraction |
| **Places** | Restaurants, cafes, attractions near a location | OpenStreetMap (Nominatim + Overpass) |
| **Web search** | General research | Serper.dev |
| **Weather** | Real forecast for any city | Open-Meteo |
| **Currency** | Live exchange-rate conversion | open.er-api.com |
| **Tasks** | Create, list, complete reminders | SQLite, isolated per user |
| **Budget** | Log and total real expenses | SQLite, isolated per user |
| **PDF parsing** | Extracts structured dates/tasks from uploaded documents | pypdf + LLM |

Every service used is genuinely free — no paid API keys anywhere in the stack.

---

## Real multi-user support

Each visitor gets their own isolated session:

- **Guests** — Tasks/Budget/Notes are private to their own browser session, no shared data between visitors
- **Logged-in users** — each person's real Google login is stored separately; when a friend signs in with their own Gmail, *their own* real calendar and email get used — fully isolated from everyone else's account
- **Rate limiting** — capped runs per session per hour, to keep the shared demo usable for everyone

---

## Frontend

A full multi-page React app (Vite + React Router):

- **Landing** — animated hero with an interactive paint-trail cursor effect, glassmorphic design, scroll-triggered reveal animations
- **Login** — real Google OAuth sign-in, or guest mode
- **Dashboard** — type a goal, watch the agent think live, see results formatted into readable cards (flights, hotels, places, weather, tasks, expenses) instead of raw JSON
- **Calendar** — real upcoming events pulled live from Google Calendar
- **Tasks** — real add/complete list
- **Budget tracker** — real expense log and running total
- **Profile** — shows your real connected Google account

---

## Tech stack

**Backend:** Python · FastAPI · LangGraph · LangChain · SQLite · WebSockets
**Frontend:** React · Vite · React Router · Canvas API
**LLM:** configurable across NVIDIA NIM, OpenRouter, and Hugging Face Inference
**External APIs:** Google Calendar, Gmail, Serper.dev, OpenStreetMap, Open-Meteo, open.er-api.com
**Deployment:** Render (backend) + Cloudflare Pages (frontend)
**Cost:** $0 — every service used has a genuinely free tier

---

## Running it locally

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
# add your own API keys to a .env file (see .env.example)
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

You'll need your own free API keys for: an LLM provider (NVIDIA NIM / OpenRouter / Hugging Face), Serper.dev, and a Google Cloud OAuth client (Calendar + Gmail scopes). See `.env.example` in `backend/` for the full list of required variables.

> The live production backend URL is intentionally not published in this repo to prevent abuse of shared API quotas. Use the [live demo](https://shundo.pages.dev) to try Shundo without running it yourself, or spin up your own backend locally with your own keys.

---

## Known limitations

- Travel pricing (flights/hotels) is extracted from live search snippets by an LLM rather than a dedicated fares API — real fare APIs gate access behind commercial accounts not practical to acquire during the build window. Prices are representative, occasionally imprecise.
- Free-tier LLM inference has variable latency depending on provider load at the time.
- Google OAuth login currently requires each user to be within the app's consent screen limits, since it hasn't gone through Google's full verification review.

---

## Contributors

- **Maddineni Renu Sri**
- **bhavana0000000**
- **karthik26-Thalari**
- **Tanmayee1802**

---

## License

MIT License

Copyright (c) 2026 Maddineni Renu Sri, bhavana0000000, karthik26-Thalari, Tanmayee1802

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
