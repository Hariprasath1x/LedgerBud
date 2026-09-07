# 💼 LedgerBud — Personal Finance Intelligence Platform

A production-ready personal finance platform with AI-powered insights, built on **FastAPI** (backend) and **Streamlit** (frontend).

---

## ✨ Features

### Core
- **Multi-Wallet Management** — Bank, Credit Card, UPI, Cash wallets with real-time balances
- **Transaction Tracking** — Full CRUD with categories, merchants, search & filtering
- **Inter-Wallet Transfers** — Move funds between wallets with automatic double-entry bookkeeping
- **Statement Import** — Upload PDF/CSV/Excel bank statements with intelligent parsing

### Planning
- **Budgets** — Category-based monthly budgets with utilization tracking (healthy → warning → exceeded)
- **Savings Goals** — Set targets, track contributions, visualize progress
- **Subscription Detection** — Auto-detect recurring payments from transaction patterns

### Intelligence
- **Financial Dashboard** — Income vs expense trends, category breakdowns, top merchants
- **Health Score** — Composite financial health rating (A–F) with actionable suggestions
- **Smart Insights** — AI-generated spending alerts, month-over-month anomaly detection
- **Net Worth Tracker** — Track assets & liabilities with point-in-time snapshots
- **FIRE Planner** — Financial Independence / Retire Early calculator with 10-step engine
- **AI Financial Advisor** — Chat with an LLM-powered advisor using your real financial data
- **Analytics** — Trend analysis, category deep-dives, what-if scenarios

---

## 🏗️ Architecture

```
┌─────────────────┐      HTTP/JSON       ┌──────────────────┐
│  Streamlit UI   │ ◄──────────────────► │  FastAPI Backend  │
│  (port 8501)    │                      │  (port 8000)      │
└─────────────────┘                      └────────┬─────────┘
                                                  │
                                         ┌────────▼─────────┐
                                         │  PostgreSQL 15    │
                                         │  (port 5432)      │
                                         └──────────────────┘
```

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.56.0, Plotly |
| Backend API | FastAPI 0.109, Uvicorn, Pydantic v2 |
| Database | PostgreSQL 15 (Docker) / SQLite (local dev) |
| ORM | SQLAlchemy 2.0 (async-ready, declarative mapped columns) |
| Auth | JWT (PyJWT + bcrypt), optional Firebase Auth |
| AI | Groq LLM API (openai/gpt-oss-120b) |
| Import Engine | pdfplumber, pandas, openpyxl |

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone and start
git clone https://github.com/your-username/ledgerbud.git
cd ledgerbud

# Start all services (PostgreSQL + App)
docker compose up -d --build

# Wait ~20 seconds for startup, then open:
#   Frontend UI:  http://localhost:8501
#   Backend API:  http://localhost:8000
#   API Docs:     http://localhost:8000/docs
```

### Local Development (No Docker)

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
#    Edit .env and uncomment/add DATABASE_URL for your preferred DB:
#    DATABASE_URL=sqlite:///./ledgerbud.db          (simplest)
#    DATABASE_URL=postgresql://user:pass@localhost:5432/ledgerbud

# 4. Start the application
python start_servers.py

# Open http://localhost:8501 in your browser
```

---

## ⚙️ Configuration

All configuration is managed via environment variables (`.env` file or Docker environment).

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(set in docker-compose)* | Database connection string |
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret for JWT token signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifetime |
| `AUTO_CREATE_TABLES` | `true` | Auto-create DB tables on startup |
| `FASTAPI_BASE_URL` | `http://localhost:8000` | URL Streamlit uses to reach the API |
| `GROQ_API_KEY` | *(empty)* | Groq API key for AI Advisor & FIRE Coach |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Target Groq model for AI services |
| `USE_FIREBASE` | `false` | Enable Firebase Authentication |
| `FIREBASE_API_KEY` | *(empty)* | Firebase Web API Key |
| `FIREBASE_PROJECT_ID` | *(empty)* | Firebase Project ID |

---

## 📁 Project Structure

```
ledgerbud/
├── app/
│   └── fastapi_app/           # FastAPI backend
│       ├── api/
│       │   ├── deps.py        # Dependency injection (auth, DB session)
│       │   └── routes/        # API route handlers
│       ├── core/              # Config, security, logging, Firebase
│       ├── db/                # SQLAlchemy engine & session
│       ├── exceptions/        # Global exception handlers
│       ├── models/            # SQLAlchemy ORM models
│       ├── repositories/      # Data access layer
│       ├── schemas/           # Pydantic request/response schemas
│       ├── services/          # Business logic layer
│       └── main.py            # FastAPI app factory
├── ui/                        # Streamlit frontend
│   ├── api_client.py          # HTTP client for FastAPI
│   ├── auth.py                # Login/Register page
│   ├── navigation.py          # Multi-page routing
│   ├── state.py               # Session state manager
│   ├── components/            # Reusable UI components
│   └── pages/                 # Individual page modules
├── streamlit_app.py           # Streamlit entry point
├── run_fastapi.py             # Uvicorn launcher
├── start_servers.py           # Dual-server orchestrator
├── docker-compose.yml         # Docker services (web + db)
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
└── .env                       # Environment configuration
```

---

## 🔌 API Documentation

Once running, interactive API documentation is available at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Sign in (returns JWT) |
| GET | `/api/v1/dashboard` | Full dashboard payload |
| GET/POST | `/api/v1/wallets` | List / create wallets |
| GET/POST | `/api/v1/transactions` | List / create transactions |
| GET/POST | `/api/v1/budgets` | Budget management |
| GET/POST | `/api/v1/goals` | Savings goal tracking |
| GET | `/api/v1/subscriptions` | Subscription detection |
| POST | `/api/v1/imports/upload` | Statement upload |
| GET | `/api/v1/analytics/trends` | Spending trends |
| POST | `/api/v1/fire/calculate` | FIRE analysis engine |
| POST | `/api/v1/advisor/ask` | AI financial advisor |

---

## 🛠️ Development

```bash
# Rebuild Docker after code changes
docker compose up -d --build

# View logs
docker logs ledgerbud_web -f

# Reset database (fresh start)
docker compose down -v && docker compose up -d --build

# Access PostgreSQL directly
docker exec -it ledgerbud_db psql -U postgres -d ledgerbud
```

---

## 📄 License

MIT
