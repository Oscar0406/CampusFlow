<div align="center">

# CampusFlow

**AI-powered multi-agent helpdesk for university campuses**

Students and staff send free-text messages — in English, Bahasa Malaysia, or Bahasa Rojak —
and CampusFlow routes them to the right department(s), calls live data tools, and replies with
specific, actionable responses.

</div>

---

## What it does

A student types:

> *"Bro, the WiFi at the library is really slow, and I also can’t access the journal database. Also, I want to know if there are any hostel rooms available for this semester?"*

CampusFlow:
1. Reads the message and identifies **IT Support** + **Library** + **Housing** are all needed
2. Calls real tools — checks the IT known-issues list, queries live room availability, looks up database access requirements
3. Replies with specific answers: the EzProxy VPN workaround, actual available rooms with real prices, and the application deadline

All in one turn. No forms. No menu navigation.

---

## Key features

- **Multi-agent routing** — one message can involve multiple departments simultaneously
- **Tool-calling agents** — agents call typed functions to query live data, never hallucinate room IDs or prices
- **Multi-turn memory** — the system remembers gender, budget, and student ID across the conversation; follow-ups work naturally
- **Multi-university** — add a new university by creating one YAML config file, no code changes
- **Switchable LLM** — change provider (Groq, OpenAI, HuggingFace, Ollama) per university via config
- **Mock university API** — simulate a real university's SIS/Finance/Housing backend for local development
- **REST API gateway** — deploy as a service behind FastAPI with session management

---

## Departments

| Department | Handles |
|---|---|
| `maintenance` | Broken equipment, HVAC, plumbing, electrical, lifts |
| `academic` | Course registration, grade appeals, transcripts, dean letters |
| `finance` | Fees, scholarships, bursaries, payment plans, refunds |
| `it_support` | Wi-Fi, portal access, software licenses, known IT issues |
| `library` | Book availability, study rooms, fines, academic databases |
| `procurement` | Purchase requests, vendor approval, budget checks |
| `housing` | Room availability, hostel applications, rules, facilities |

---

## Architecture

```
User message (any language, any style)
        │
        ▼
┌─────────────────────────────────────────┐
│           API Gateway (FastAPI)          │
│  • X-University-Id header selects tenant │
│  • Session store (in-memory / Redis)     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           Orchestrator Service           │
│  • Sees full conversation history        │
│  • Identifies all relevant departments   │
│  • Extracts structured data per turn     │
│  • Updates session user context          │
└──────────┬──────────────────────────────┘
           │  departments: ["housing", "finance"]
           │  extracted_data: {gender, urgency, ...}
           ▼
┌─────────────────────────────────────────┐
│         Dispatcher (parallel calls)      │
│  Injects: LLMService + Repo + Adapter    │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────┐     Each agent runs an agentic loop:
│Housing│ │ Finance │     LLM decides which tools to call →
│ Agent │ │  Agent  │     calls them → inspects results →
└───┬───┘ └────┬────┘     calls more if needed → final reply
    │          │
    ▼          ▼
┌─────────────────────────────────────────┐
│              Tool Registry               │
│  get_available_rooms()                   │
│  get_scholarships_and_bursaries()        │
│  submit_housing_application()  ...       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           University Adapter             │
│  json_local  →  reads local JSON files   │
│  generic_rest → calls real/mock REST API │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           JSON Repository                │
│  data/utm/housing.json  (tickets + data) │
│  data/utm/finance.json                   │
│  ...                                     │
└─────────────────────────────────────────┘
```

---

## Quick start

### 1. Install dependencies

```bash
cd CampusFlow_v4
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
LLM_API_KEY=your_LLM_key_here
```

Everything else is optional for local development.

### 3. Run

```bash
python main.py              # interactive chat (UTM, dev mode)
python main.py --test       # run the built-in multi-turn test suite
python main.py --uni ukm    # chat as UKM instead
```

### CLI commands during chat

| Command | What it does |
|---|---|
| `exit` | Quit and save the session to `results/` |
| `new` | Start a fresh conversation |
| `tickets` | Show all tickets raised this session |
| `context` | Show user facts collected (gender, student ID, budget, etc.) |

---

## Run with the mock university API

The mock API simulates UTM's real student, finance, and housing systems so you can
develop and test without real API credentials.

**Terminal 1 — start the mock server:**
```bash
uvicorn mock_university_api.server:app --port 8001 --reload
```
Visit `http://localhost:8001/docs` to explore all available endpoints.

**Terminal 2 — run CampusFlow pointing at the mock:**
```bash
python main.py --uni utm_mock
```

Add this to your `.env`:
```env
MOCK_API_KEY=anything    # any non-empty string works
```

Your `LLM_API_KEY` is still required — the LLM is real, only the university database
is mocked.

---

## Run as a REST API

```bash
uvicorn gateway.gateway:app --reload
```

**POST** `/v1/chat`

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-University-Id: utm" \
  -d '{"message": "Is there any hostel room available for this sem?", "session_id": ""}'
```

Response:
```json
{
  "session_id": "abc-123",
  "reply": "Yes, we have rooms available across two colleges...",
  "routing": {
    "departments": ["housing"],
    "confidence": 0.97,
    "is_followup": false
  },
  "responses": { "housing": { ... } }
}
```

Pass the returned `session_id` in subsequent requests to maintain conversation context.

**Other endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/v1/universities` | List all configured universities |
| `GET` | `/v1/session/{id}` | Get session state |
| `DELETE` | `/v1/session/{id}` | Clear a session |

---

## Project structure

```
CampusFlow_v4/
├── main.py                        ← CLI entry point
├── requirements.txt
├── .env.example                   ← Copy to .env
├── CONTRIBUTING.md                ← Teammate guide (how to extend everything)
│
├── config/
│   └── universities/
│       ├── utm.yaml               ← UTM (dev mode, reads local JSON)
│       ├── utm_mock.yaml          ← UTM (mock API mode, calls localhost:8001)
│       └── ukm.yaml               ← UKM (production REST adapter)
│
├── gateway/
│   └── gateway.py                 ← FastAPI app with session management
│
├── orchestrator/
│   ├── orchestrator.py            ← Routes messages using conversation history
│   └── dispatcher.py              ← Wires LLM + repo + adapter, runs agents
│
├── agents/
│   ├── housing.py                 ← System prompt only — logic is in agent_base.py
│   ├── maintenance.py
│   └── ...                        ← One file per department
│
├── core/
│   ├── agent_base.py              ← Agentic tool-calling loop
│   ├── tools.py                   ← All tool definitions (READ + WRITE per dept)
│   └── json_parser.py
│
├── services/
│   ├── llm_service.py             ← Groq/OpenAI wrapper, config-driven
│   ├── session_store.py           ← In-memory session storage (swap for Redis)
│   └── ticket_service.py
│
├── adapters/
│   ├── json_local_adapter.py      ← Dev: reads local JSON files
│   ├── rest_adapter.py            ← Prod: calls real university REST APIs
│   └── factory.py                 ← Picks adapter from YAML config
│
├── repositories/
│   └── json_repo.py               ← Ticket storage (swap for PostgreSQL later)
│
├── models/
│   ├── session.py                 ← Conversation history + user context
│   ├── context.py                 ← TenantContext (per-university config)
│   ├── request.py                 ← IncomingRequest, RoutingDecision
│   └── ticket.py                  ← Ticket + TicketStatus
│
├── data/
│   └── utm/                       ← Reference data + ticket store for UTM
│       ├── housing.json
│       ├── academic.json
│       └── ...
│
└── mock_university_api/
    ├── server.py                  ← Simulates UTM's SIS, Finance, Housing APIs
    └── data.py                    ← Seed data: students, rooms, courses, finances
```

---

## Adding a new university

No Python code changes needed. Create one YAML file:

```yaml
# config/universities/myuni.yaml
university_id: myuni
display_name: My University

llm:
  provider: groq
  model: qwen/qwen3-32b
  api_key_env: LLM_API_KEY

departments:
  - maintenance
  - academic
  - finance
  - housing

adapters:
  type: generic_rest
  sis:
    base_url: https://sis.myuni.edu.my/api
    api_key_env: MYUNI_SIS_KEY
    schema:
      student_id: studentNo      # map their field names to CampusFlow's
      full_name: name
      programme: course
      status: enrolStatus
  ...

ticket_store:
  type: json
  path: ./data/myuni/
```

Then create `data/myuni/` with reference data and run:

```bash
python main.py --uni myuni
```

See `CONTRIBUTING.md` for the full step-by-step guide.

---

## Switching the LLM

Change two things only:

**`config/universities/utm.yaml`:**
```yaml
llm:
  provider: openai          # groq | openai | hf | ollama
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
```

**`services/llm_service.py`** — add the provider to `_PROVIDERS` dict (one-time setup per provider, not per university).

See `CONTRIBUTING.md` section 3 for the full pattern including HuggingFace and local Ollama.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | LLM API key |
| `MOCK_API_KEY` | Mock mode only | Any non-empty string |
| `LANGSMITH_API_KEY` | Optional | LangSmith tracing |
| `UTM_SIS_KEY` | Production only | UTM student system API key |
| `UTM_FIN_KEY` | Production only | UTM finance system API key |
| `UTM_HSG_KEY` | Production only | UTM housing system API key |

---

## Requirements

- Python 3.11+
- LLM API key
- No database setup required for local development

---
