# PlanMyTrip AI — Enterprise Multi-Agent Travel Orchestration Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard-4A154B?style=for-the-badge)](https://modelcontextprotocol.io/)

**PlanMyTrip AI** is a multi-agent travel orchestration engine built with **LangGraph**, **FastAPI**, **PostgreSQL 16**, **Redis 7**, and the **Model Context Protocol (MCP)**. It transforms travel requests into comprehensive, budget-reconciled, and temporally verified itineraries using live real-world APIs, multi-stage parallel agent fan-out, and a real-time responsive web interface.

---

## Key Highlights & Architectural Features

### 1. Two-Stage Multi-Agent Orchestration (LangGraph)
Unlike naive single-prompt LLM wrappers, PlanMyTrip AI executes an coordinated 2-stage workflow:
- **Stage 1 — Parallel Domain Fan-Out**: [FlightAgent](file:///d:/Study/PlanMyTrip-AI/backend/app/agents/flight_agent.py), [PlacesAgent](file:///d:/Study/PlanMyTrip-AI/backend/app/agents/places_agent.py), and [ItineraryAgent](file:///d:/Study/PlanMyTrip-AI/backend/app/agents/itinerary_agent.py) run simultaneously in `asyncio.gather`, querying live flight schedules, daytime sightseeing clusters, and weather outlooks.
- **Stage 2 — Location-Grounded Hotel & Dining Matching**: [HotelAgent](file:///d:/Study/PlanMyTrip-AI/backend/app/agents/hotel_agent.py) executes **after** PlacesAgent extracts the destination's primary daytime activity hub (`target_stay_neighborhood`). Stays and lunch/dinner recommendations are spatially anchored to where the traveler actually spends their days.

### 2. Single-Base Stay Strategy (Luggage-Free Precaution)
When a traveler visits attractions within the same destination or city over multiple days:
- The system automatically selects a central base hotel for check-in on **Day 1**.
- Across intermediate nights (**Day 2 to Day $N-1$**), the traveler remains in the same room (`Luggage stays in room - no hotel change needed`), completely eliminating the hassle of packing, checking out, and hauling luggage across town every morning.
- On **Day $N$**, the itinerary schedules check-out with luggage stored at the hotel concierge until the evening departure flight.

### 3. Post-Generation Output Guardrail & Verification Loop
Before final rendering, [synthesis_agent.py](file:///d:/Study/PlanMyTrip-AI/backend/app/agents/synthesis_agent.py) passes the synthesized itinerary through an automated requirement verifier:
- **Strict $N$-Day Guarantee**: Mathematically verifies that every requested day ($1 \dots N$) is explicitly generated without skipped dates.
- **Inclusive Calendar Arithmetic**: Correctly calculates $D_{\text{end}} = D_{\text{start}} + N - 1$.
- **Flight & Stay Alignment**: Ensures Day 1 begins with arrival telemetry and Day $N$ concludes with the verified return flight leg.
- **No Hallucinated Rates**: Keeps hotel rates grounded in real check-in/out durations without rate inflation.

### 4. Deterministic Financial Reconciliation
- All monetary arithmetic is executed with Python `decimal.Decimal` and ISO-4217 currency tracking (`backend/app/core/money.py`).
- [budget_reconciler.py](file:///d:/Study/PlanMyTrip-AI/backend/app/services/budget_reconciler.py) produces verified cost breakdowns across budget tiers (Budget / Moderate / Luxury) by strictly summing real components ($\text{Total} = \text{Flights} + \text{Hotels} + \text{Transit/Daily}$) with zero floating-point drift.

### 5. Live Travel APIs & Credit-Safe Caching
PlanMyTrip AI integrates real-world travel APIs while protecting free-tier credits:
- **FlightAPI.io**: Real-time round-trip and one-way airfare searches mapped to operating carriers (IndiGo, Air India, SpiceJet, Akasa) with an in-memory cache and a strict $\le 3$ carrier limit per search.
- **SerpApi Google Hotels**: Live hotel rates, exact INR prices, star ratings, and neighborhood filtering.
- **Tavily Search**: Real-time daytime attractions and curated lunch & dinner dining recommendations.
- **Open-Meteo**: Microclimate forecast telemetry for precipitation, temperature, and packing tips.

### 6. Real-Time Visual Progress Box (Modern Glassmorphic UI)
- The frontend replaces raw debug messages with a live agent progress container.
- An animated spinner tracks ongoing agent activities, displaying real-time green checkmarks (**✅**) as each agent (Flights, Places, Weather, Hotels, Synthesis) completes its task.
- Zero-build Vanilla HTML5, CSS3, and ES6 JavaScript consuming Server-Sent Events (SSE) directly.

### 7. Human-in-the-Loop (HITL) Checkpoints & Relational Security
- LangGraph checkpoints are backed by PostgreSQL via `AsyncPostgresSaver`.
- **Relational Thread Ownership**: Every thread is cryptographically bound to an authenticated `user_id`, preventing unauthorized state access.
- Users can review, edit, or approve recommendations interactively before committing.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Vanilla SPA)"]
        UI["Modern Glassmorphic UI\n(SSE / REST)"]
    end

    subgraph Backend ["FastAPI Application Engine (Port 8000)"]
        AUTH["JWT Authentication & RBAC"]
        GUARD["Input Guardrail (Topic & Safety)"]
        INTAKE["Intake Supervisor (Gateway & Dates)"]
        RECON["Deterministic Budget Reconciler"]
    end

    subgraph StateMachine ["LangGraph 2-Stage Multi-Agent Graph"]
        ORCH["Workers Orchestrator"]
        
        subgraph Stage1 ["Stage 1: Parallel Fan-Out"]
            FLIGHT["Flight Agent"]
            PLACES["Places & Attractions Agent"]
            WEATHER["Itinerary & Weather Agent"]
        end
        
        subgraph Stage2 ["Stage 2: Location-Grounded Execution"]
            HOTEL["Hotel & Dining Agent\n(Target Neighborhood Matching)"]
        end
        
        SYNTH["Synthesis Agent & Output Verifier\n(N-Day Guarantee & Single-Base Continuity)"]
    end

    subgraph MCP ["Model Context Protocol Servers"]
        F_MCP["Flight MCP (Port 8001)\nFlightAPI.io + In-Memory Cache"]
        W_MCP["Weather MCP (Port 8002)\nOpen-Meteo Forecasts"]
        P_MCP["Places MCP (Port 8003)\nSerpApi Google Hotels + Tavily Dining"]
    end

    subgraph Storage ["Persistence & Cache"]
        PG[("PostgreSQL 16 (Port 5434)\nUsers, Trips, LangGraph Checkpoints")]
        RD[("Redis 7 (Port 6380)\nCircuit Breakers & Session Cache")]
    end

    UI -->|HTTP / SSE| AUTH
    AUTH --> GUARD
    GUARD --> INTAKE
    INTAKE --> ORCH

    ORCH --> FLIGHT
    ORCH --> PLACES
    ORCH --> WEATHER

    FLIGHT <-->|HTTP MCP| F_MCP
    WEATHER <-->|HTTP MCP| W_MCP
    PLACES <-->|HTTP MCP| P_MCP

    PLACES -.->|target_stay_neighborhood| HOTEL
    ORCH --> HOTEL
    HOTEL <-->|HTTP MCP| P_MCP

    FLIGHT --> SYNTH
    PLACES --> SYNTH
    WEATHER --> SYNTH
    HOTEL --> SYNTH

    SYNTH --> RECON
    RECON --> UI

    StateMachine <--> PG
    Backend <--> RD
```

---

## Microservices & Port Topology

| Service | Host / Port | Protocol | Description |
| :--- | :--- | :--- | :--- |
| **Main Web & API Engine** | `http://localhost:8000` | HTTP / SSE | FastAPI application engine & Static Vanilla SPA frontend |
| **Flight MCP Server** | `http://localhost:8001` | HTTP / MCP | FlightAPI.io live search, carrier normalization, fallback provider |
| **Weather MCP Server** | `http://localhost:8002` | HTTP / MCP | Open-Meteo real-time forecasts, precipitation & temperatures |
| **Places & Hotels MCP** | `http://localhost:8003` | HTTP / MCP | SerpApi Google Hotels, Tavily attractions, local dining tools |
| **PostgreSQL Database** | `localhost:5434` | PostgreSQL Wire | User credentials, trips, and LangGraph `AsyncPostgresSaver` |
| **Redis Cache** | `localhost:6380` | RESP | Circuit breakers, session caches, and rate-limiting |

---

## Repository Structure

```text
PlanMyTrip-AI/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── flight_agent.py          # Flight research & carrier selection
│   │   │   ├── hotel_agent.py           # Location-grounded hotel & dining agent
│   │   │   ├── intake_agent.py          # Gateway resolver & date math supervisor
│   │   │   ├── itinerary_agent.py       # Weather integration & day-by-day outline
│   │   │   ├── places_agent.py          # Attractions cluster & target stay neighborhood
│   │   │   └── synthesis_agent.py       # Deterministic N-day verifier & final synthesis
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py              # User authentication, JWT login & signup
│   │   │       ├── hitl.py              # Human-in-the-loop checkpoint resumption
│   │   │       └── trips.py             # SSE trip planning & history endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Strictly-typed Pydantic settings
│   │   │   ├── money.py             # Decimal financial arithmetic
│   │   │   └── state.py             # LangGraph shared state schema
│   │   ├── graph/
│   │   │   ├── builder.py           # 2-stage LangGraph builder & node wiring
│   │   │   └── edges.py             # Conditional routing functions
│   │   ├── guardrails/
│   │   │   └── input_guard.py       # Safety, jailbreak, & domain validation
│   │   └── services/
│   │       └── budget_reconciler.py # Multi-tier Decimal budget reconciliation
│   └── scripts/
│       ├── run_mcp_servers.py       # Concurrent launcher for all 3 MCP servers
│       ├── seed_demo_user.py        # Demo user seeder script
│       └── smoke_test_graph.py      # End-to-end integration test
├── frontend/
│   ├── app.js                       # Frontend state machine & SSE progress box
│   ├── index.html                   # Landing page
│   ├── login.html / signup.html     # Auth pages
│   ├── main.html                    # Interactive trip planner dashboard
│   ├── styles.css                   # Glassmorphic responsive design system
│   └── trips.html / trips.js        # Past trip viewer & detail inspector
├── mcp_servers/
│   ├── flight_server.py             # FlightAPI.io MCP tool server (Port 8001)
│   ├── weather_server.py            # Open-Meteo MCP tool server (Port 8002)
│   └── places_server.py             # SerpApi Google Hotels MCP server (Port 8003)
├── docker-compose.yml               # PostgreSQL 16 & Redis 7 container specs
├── run_all.py                       # Single-command orchestrator for all services
└── README.md
```

---

## Quickstart Guide

### 1. Prerequisites
- **Python 3.11+** or **Python 3.12+**
- **Docker Desktop** (for PostgreSQL 16 & Redis 7)
- API Keys for OpenAI, FlightAPI.io, SerpApi, and Tavily (optional fallback options are provided automatically)

### 2. Infrastructure Setup
Start the containerized PostgreSQL and Redis instances:
```bash
docker compose up -d
docker compose ps
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

| Variable | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | Required. OpenAI API key (`sk-proj-...`). |
| `FLIGHTAPI_KEY` | Required for live airfare search on FlightAPI.io. |
| `SERPAPI_API_KEY` | Required for live Google Hotels and dining search. |
| `TAVILY_API_KEY` | Required for live attractions and local dining options. |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://postgres:postgres@localhost:5434/planmytrip`). |
| `REDIS_URL` | Redis connection URI (`redis://localhost:6380/0`). |
| `JWT_SECRET` | 32+ character cryptographic secret for signing auth tokens. |

### 4. Install Dependencies & Seed Database
```bash
# Activate your virtual environment
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux / macOS

# Seed the default demo user (demo@planmytrip.ai / password123)
python backend/scripts/seed_demo_user.py
```

---

## Running the Application

### Option A: One-Command Startup (Recommended)
Launch the entire system (all 3 MCP servers + FastAPI backend + auto-open web UI):
```bash
python run_all.py
```

### Option B: Manual Startup (Separate Terminals)

1. **Terminal 1 — Launch MCP Servers:**
   ```bash
   python backend/scripts/run_mcp_servers.py
   ```
2. **Terminal 2 — Launch Backend & Web Server:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

## Accessing the Web Application

1. Open **`http://localhost:8000`** in your browser.
2. Log in using the seeded demo credentials:
   - **Email**: `demo@planmytrip.ai`
   - **Password**: `password123`
3. Click **+ New Trip** and enter your desired trip details (e.g. *"Plan a 5-day trip to Ahmedabad from Mumbai for 2 people with a moderate budget"*).
4. Watch the **Live Agent Progress Box** update in real time with animated green checkmarks (**✅**) across all agent stages.

---

## Verification & Testing

Verify end-to-end multi-agent execution, checkpointer persistence, and financial reconciliation:
```bash
python backend/scripts/smoke_test_graph.py
```

Verify MCP Server tool definitions:
```bash
# Flight MCP (8001)
curl http://localhost:8001/tools

# Weather MCP (8002)
curl http://localhost:8002/tools

# Places & Hotels MCP (8003)
curl http://localhost:8003/tools
```

---

## Security Notice & Non-Goals

- **Indicative Estimates Only**: This system generates travel plans and price estimations. It does not execute live bookings, charge cards, or store banking credentials.
- **Zero PII Storage**: The system only stores the user's login email and hashed password (`bcrypt`).
- **Secret Discipline**: Sensitive API keys and tokens are stored exclusively in `.env` and excluded from version control via `.gitignore`.
