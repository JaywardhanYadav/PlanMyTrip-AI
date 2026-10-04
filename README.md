# PlanMyTrip AI — Enterprise Multi-Agent Travel Planning System

PlanMyTrip AI is an enterprise-grade multi-agent travel orchestration engine built with LangGraph, FastAPI, PostgreSQL 16, Redis 7, and the Model Context Protocol (MCP). It features strictly typed Pydantic V2 state models, deterministic financial arithmetic, parallel fan-out research agents, Human-In-The-Loop (HITL) checkpoints, and token-streaming SPAs.

---

## Non-Goals & Security Notice

- **Indicative Estimates Only**: This system produces travel plans and estimates. It never executes real bookings, charges credit cards, or processes financial transactions. All prices are indicative estimates and labeled as such across all outputs.
- **Privacy & PII**: This system never stores user PII beyond an authentication email and hashed credentials.
- **Secret Discipline**: Any API key or secret ever committed to version control is permanently burned and must be rotated immediately.

---

## Architectural Highlights

1. **Strictly Typed State Machine (Layer 1)**: Replaces loose string blobs with Pydantic V2 models (`FlightOption`, `HotelOption`, `ActivityOption`, `WeatherOutlook`, `TripBudget`).
2. **Idempotent Keyed Reducers**: Custom `keyed_option_merge` reducer prevents duplicate flights, hotels, and activities when resuming from Human-In-The-Loop interrupts.
3. **Deterministic Financial Reconciliation**: All monetary values are `decimal.Decimal` with ISO-4217 currencies. Zero floating-point drift.
4. **Relational Thread Ownership (Layer 2 - Defect #14 Remediation)**: Every LangGraph `thread_id` is cryptographically bound to an authenticated `user_id` via PostgreSQL, preventing unauthorized state reads and resumes.
5. **Decoupled Tool Protocol**: All external vendor data (flight schedules, weather forecasts, attractions) is queried via standalone MCP servers communicating over Streamable HTTP.
6. **Zero-Build Vanilla SPA (Layer 3)**: Pure HTML5/CSS3/ES6 JavaScript frontend consuming Server-Sent Events (SSE) directly for real-time streaming, interactive option cards, and HITL approve/edit panels.

---

## System Architecture

```
                       ┌────────────────────────┐
                       │  Vanilla HTML5/JS SPA  │
                       └───────────┬────────────┘
                                   │ SSE / REST (JWT Auth)
                                   ▼
                       ┌────────────────────────┐
                       │   FastAPI App Engine   │
                       └─────┬────────────┬─────┘
                             │            │
             SQLAlchemy 2.0  │            │ AsyncPostgresSaver
           (Users, Trips)    │            │ (Checkpoints)
                             ▼            ▼
                       ┌────────────────────────┐
                       │ PostgreSQL 16 / Redis  │
                       └────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ LangGraph Multi-Agent Engine │
                    └──────────────┬───────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
     │ Flight Agent  │     │  Hotel Agent  │     │Itinerary Agent│
     └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
             │                     │                     │
             ▼                     ▼                     ▼
     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
     │ Flight MCP    │     │  Places MCP   │     │  Weather MCP  │
     │ (Port 8001)   │     │  (Port 8003)  │     │  (Port 8002)  │
     └───────────────┘     └───────────────┘     └───────────────┘
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+ (or Python 3.12 managed via `uv`)
- Docker Desktop (PostgreSQL 16 & Redis 7)

### 2. Infrastructure Setup
```bash
# Start PostgreSQL (Port 5434) and Redis (Port 6380)
docker compose up -d

# Verify containers are healthy
docker compose ps
```

### 3. Environment Setup
```bash
# Configure secrets
copy .env.example .env

# Activate Python 3.12 virtual environment
.venv\Scripts\activate

# Seed demo user credentials (demo@planmytrip.ai / password123)
python backend/scripts/seed_demo_user.py
```

### 4. Running the System

#### Option A: Quickstart (All Services in 1 Command)
```bash
python run_all.py
```
This starts all 3 MCP servers (8001, 8002, 8003), launches the FastAPI backend and Web SPA (8000), and automatically opens `http://localhost:8000` in your browser.

#### Option B: Run Services Individually

1. **Start the MCP Servers:**
```bash
python backend/scripts/run_mcp_servers.py
```

2. **Start the FastAPI Backend & Web SPA:**
```bash
python -m uvicorn app.main:app --port 8000
```

#### Access the Web App
Open `http://localhost:8000` in your browser. Log in with:
- **Email**: `demo@planmytrip.ai`
- **Password**: `password123`

Click **+ New Trip**, enter your destination, and watch the multi-agent graph stream parallel research, present interactive option cards, and await your Human-in-the-Loop review!

---

## Testing & Verification

Run the end-to-end integration smoke test proving parallel fan-out, PostgreSQL checkpointer persistence, and HITL state resumption:
```bash
python backend/scripts/smoke_test_graph.py
```
