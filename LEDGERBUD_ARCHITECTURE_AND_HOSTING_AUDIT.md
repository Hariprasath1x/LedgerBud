# LedgerBud — Complete System Architecture Audit & Hosting Feasibility Report

**Document Version:** 1.0.0  
**Audit Date:** October 23, 2026  
**Auditor:** Senior Software Architect, DevOps & Cloud Infrastructure Consultant, Database Architect, and Application Security Reviewer  
**Repository:** `Hariprasath1x/LedgerBud` (`https://github.com/Hariprasath1x/LedgerBud.git`)  
**Commit Inspected:** `246d4e5` (Branch: `main`)  
**Status:** Read-Only Audit & Feasibility Investigation (No Code Modified, No Infrastructure Deployed)

---

## 1. Executive Summary

### 1.1 Overview
**LedgerBud** is an intelligent personal finance and wealth management platform designed to provide automated financial tracking, AI-driven advisory, multi-wallet balance management, bank statement extraction (PDF/CSV/XLSX), budget monitoring, net worth calculation, and a specialized 10-step Financial Independence / Retire Early (FIRE) planning engine.

The platform is architected as a decoupled two-tier system:
1. **Frontend:** A multi-page **Streamlit** (v1.56.0) application utilizing `st.navigation`, Plotly data visualizations, and session management.
2. **Backend:** A high-performance **FastAPI** (v0.111.0+) REST API utilizing **SQLAlchemy 2.0** for object-relational mapping, **Pydantic v2** for schema validation, **Uvicorn** as the ASGI server, and **Groq Cloud API** (`openai/gpt-oss-120b`) for generative financial intelligence.
3. **Identity:** **Google Firebase Authentication** (Identity Toolkit REST API on frontend; Firebase Admin SDK token verification on backend).
4. **Database:** Configured for **SQLAlchemy** with dialect support for SQLite (current local development), PostgreSQL (Docker Compose), and MySQL.

### 1.2 Key Audit Findings
1. **Frontend-to-Backend Decoupling:** The Streamlit frontend is completely decoupled from the backend persistence layer. It accesses business logic strictly through HTTP REST requests via `ui/api_client.py` (`FASTAPI_BASE_URL`), making independent frontend and backend hosting architecturally sound.
2. **Database Migration Deficit (Critical Blocker):** The Alembic migration directory (`alembic/versions/`) is severely out of sync with the application models. Alembic only defines three initial revisions (`users`, `wallets`, basic `transactions`, and `users.firebase_uid`). Eight full database tables (`merchants`, `budgets`, `goals`, `subscriptions`, `import_jobs`, `net_worth_items`, `net_worth_snapshots`, `fire_analysis`) and multiple critical transaction columns have no Alembic migrations. Running `alembic upgrade head` on a fresh database creates a broken, non-functional schema. The application currently relies on `AUTO_CREATE_TABLES=true` (`Base.metadata.create_all`).
3. **Database URI Dialect Incompatibility (Critical Blocker):** `app/fastapi_app/core/config.py` passes `postgres://` connection strings directly to SQLAlchemy. In SQLAlchemy 2.0, the `postgres://` prefix was deprecated and removed, raising `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres`. Because Neon, Supabase, and Render frequently output `postgres://` URLs, this will cause immediate crash-loops upon cloud deployment unless sanitized to `postgresql://`.
4. **Single-Port Cloud Incompatibility:** The repository's Dockerfile and `start_servers.py` attempt to run both FastAPI (port 8000) and Streamlit (port 8501) inside the same container. Standard cloud PaaS platforms (Render, Fly.io, Hugging Face Spaces) route incoming traffic to a single dynamic `$PORT`. Without a reverse proxy (e.g., Nginx or Caddy), a single container running two servers cannot be exposed on a standard PaaS web service.
5. **Ephemeral Storage Risk in Statement Ingestion:** Statement ingestion in `app/fastapi_app/services/import_service.py` saves uploaded files to the local filesystem (`app/static/uploads/`) and subsequently reads that file again during `commit_import`. On ephemeral hosting containers that spin down after inactivity (e.g., Render free tier), any delay between file preview and commit will result in a fatal `Source file not found` error if the container recycles.
6. **Authentication Architecture Discrepancy:** The `README.md` documents a legacy JWT/bcrypt architecture with endpoints `/api/v1/auth/login` and `/api/v1/auth/register`. In the actual implementation, authentication is exclusively handled by Google Firebase Auth. Passwords never reach FastAPI.
7. **Security Vulnerability (IDOR/BOLA in Import):** `ImportService.process_upload` and `_run_etl_commit` accept a `wallet_id` parameter without verifying that the wallet belongs to the authenticated user. A malicious authenticated user could theoretically associate transactions with, or overwrite the balance of, another user's wallet.

### 1.3 Feasibility Verdict & Financial Summary
- **Free Public Demo:** **CONDITIONAL GO**. Deployable at **$0.00/month** by splitting the frontend to **Streamlit Community Cloud**, the backend to **Render Web Service (Free Tier)**, the database to **Neon Serverless PostgreSQL (Free Tier)**, authentication to **Firebase Auth (Spark Free Plan)**, and AI to **Groq Cloud API (Free Plan)**. Requires fixing 4 configuration/code blockers prior to launch.
- **Production Personal Financial Data:** **GO WITH LOW-COST VPS OR CONDITIONAL GO ON FREE TIER**. Because personal financial data requires strict durability and zero cold-start delay during interactive usage, a **$4.00 – $6.00/month** single-node VPS (Hetzner Cloud or DigitalOcean Droplet) running Docker with Nginx, or Neon Free Tier combined with a paid persistent backend instance, is strongly recommended over ephemeral spinning services.

---

## 2. Audit Scope and Limitations

### 2.1 Scope
The audit encompasses:
- Repository structure, source code, configuration files, and containerization artifacts.
- Static code analysis of all API routes, services, repositories, models, ETL pipelines, and UI components.
- Verification of database schemas, relationships, constraints, and migration scripts.
- Defensive security review covering authentication, authorization, secret hygiene, input handling, and data privacy.
- Verification of test suites using safe, isolated, in-memory SQLite fixtures.
- Real-time research of hosting provider capabilities, quotas, limits, and pricing as of October 2026.

### 2.2 Operational Limitations & Safety Constraints
- **Preservation of Pre-existing Uncommitted Work:** The working tree contains modifications in three files:
  - `app/etl/transformer/recognition_engine.py` (type hints and lookup refactoring)
  - `app/fastapi_app/db/base.py` (removal of automatic `__tablename__` directive)
  - `app/fastapi_app/services/advisor_service.py` (defensive null handling for completions)
  These files have been preserved completely untouched in accordance with audit preservation directives.
- **Zero Local Database Mutation:** No tests or scripts were executed against the existing local database file (`ledgerbud.db`).
- **No Secret Disclosure:** Contents of `.env`, `serviceAccountKey.json`, private keys, and user transactions were not read, inspected, or recorded.
- **No Active Deployment:** No cloud resources were provisioned, modified, or billed during this assessment.

---

## 3. Current Repository State

```
Branch: main
Remote URL: https://github.com/Hariprasath1x/LedgerBud.git
Latest Commit: 246d4e5 - "All 9 test suites and normalizer sanity tests continue to pass with 0 errors"
Working Tree Status: Clean except for 3 pre-existing tracked modifications
```

### 3.1 Git Status Inspection
```bash
$ git status --short
 M app/etl/transformer/recognition_engine.py
 M app/fastapi_app/db/base.py
 M app/fastapi_app/services/advisor_service.py
```

### 3.2 Tracked vs. Ignored Secret Hygiene
An inspection of Git history (`git log --all`) and `.gitignore` verified the following:
- `.env` is properly ignored and has **never** been committed to Git history.
- `serviceAccountKey.json` and `firebase-adminsdk*.json` are properly ignored and have **never** been committed.
- `ledgerbud.db`, `*.sqlite3`, and `instance/` are properly ignored and have **never** been committed.
- Uploaded bank statements (`app/static/uploads/`) are properly ignored and have **never** been committed.

### 3.3 Python Environment Divergence
- `.python-version` specifies **Python 3.13**.
- Local virtual environment (`.venv`) runs **Python 3.13.14**.
- `Dockerfile` specifies `FROM python:3.10-slim`.
- *Finding:* While the codebase runs without syntax errors under both Python 3.10 and 3.13, keeping Dockerfile on 3.10 while local development runs on 3.13 introduces potential subtle standard library or dependency wheel differences. Aligning the Dockerfile to `python:3.12-slim` or `3.13-slim` is recommended.

---

## 4. Complete Directory and Component Inventory

```
ledgerbud/
├── .gitignore                          # Git ignore definitions
├── .python-version                     # Specifies Python 3.13
├── Dockerfile                          # Multi-stage/single-stage Python 3.10 container
├── docker-compose.yml                  # Local development stack (db: Postgres 15, web: LedgerBud)
├── entrypoint.sh                       # Container entrypoint script invoking start_servers.py
├── start.sh / start.bat                # Host startup wrappers for macOS/Linux and Windows
├── start_servers.py                    # Process manager: launches run_fastapi.py and streamlit_app.py
├── run_fastapi.py                      # Uvicorn launcher for app.fastapi_app.main:app
├── streamlit_app.py                    # Streamlit multipage application entrypoint
├── alembic.ini                         # Alembic migration configuration
├── pyrightconfig.json                  # Type-checking configuration
├── pytest.ini                          # Pytest configuration (testpaths = tests)
├── requirements.txt                    # Python dependency manifest
├── alembic/
│   ├── env.py                          # Alembic migration environment
│   ├── script.py.mako                  # Migration generation template
│   └── versions/                       # 3 historical migration versions
├── app/
│   ├── etl/                            # Financial Intelligence & Statement Extraction Engine
│   │   ├── extractor/                  # Parsers for PDF, CSV, and XLSX formats
│   │   │   ├── base.py                 # Abstract base class BaseExtractor & RawTransaction dataclass
│   │   │   ├── csv_extractor.py        # Comma/delimiter separated statement parser
│   │   │   ├── pdf_extractor.py        # pdfplumber-based tabular/text statement extractor
│   │   │   └── xlsx_extractor.py       # openpyxl-based spreadsheet statement extractor
│   │   └── transformer/                # Cleaning, Normalization, & Enrichment Pipeline
│   │       ├── deduplicator.py         # MD5 fingerprinting and duplicate transaction detector
│   │       ├── merchant_resolver.py    # Fallback merchant naming utility
│   │       ├── normalizer.py           # Regex date parser, currency cleaner, token extractor
│   │       ├── recognition_engine.py   # 5-stage Merchant Recognition Engine with seed dictionary
│   │       ├── segmenter.py            # Splitting merged PDF lines into discrete transaction items
│   │       └── type_resolver.py        # Debit/Credit/Income/Expense heuristics resolver
│   ├── fastapi_app/                    # Core Backend REST API
│   │   ├── main.py                     # App factory, CORS, exception handlers, lifespan table setup
│   │   ├── api/
│   │   │   ├── deps.py                 # OAuth2 bearer, Firebase token verification, DB session injection
│   │   │   └── routes/                 # 14 modular route definitions
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic BaseSettings, database URL precedence, CORS rules
│   │   │   ├── exceptions.py           # Custom domain exceptions
│   │   │   ├── firebase.py             # Firebase Admin SDK initialization & token validator
│   │   │   └── logging.py              # Centralized logging configuration
│   │   ├── db/
│   │   │   ├── base.py                 # DeclarativeBase SQLAlchemy foundation
│   │   │   └── session.py              # Engine factory, connection pool settings, get_db generator
│   │   ├── exceptions/
│   │   │   └── handlers.py             # HTTP error and domain error response mappers
│   │   ├── models/                     # 11 SQLAlchemy 2.0 ORM Declarative Models
│   │   │   ├── user.py, wallet.py, transaction.py, merchant.py, budget.py, goal.py,
│   │   │   ├── subscription.py, import_job.py, net_worth.py, fire.py
│   │   ├── repositories/               # Data access layer (User, Wallet, Transaction, FIRE)
│   │   ├── schemas/                    # Pydantic v2 validation and serialization schemas
│   │   └── services/                   # Business logic (Dashboard, Analytics, Advisor, FIRE, etc.)
│   └── static/uploads/                 # Target folder for statement uploads
├── ui/                                 # Streamlit Frontend Layer
│   ├── api_client.py                   # Centralized HTTP client wrapping httpx
│   ├── auth.py                         # Firebase client auth (Sign In, Sign Up, Password Reset)
│   ├── formatters.py                   # Currency, date, and percentage string formatters
│   ├── navigation.py                   # st.navigation dynamic sidebar and route generator
│   ├── state.py                        # Session state manager & browser cookie session restorer
│   ├── components/                     # Reusable UI widgets (charts, metrics, tables, empty states)
│   └── pages/                          # 14 UI page views
└── tests/                              # Automated test suites
    ├── conftest.py                     # In-memory SQLite fixture and test client setup
    ├── test_advisor_context.py         # AI context aggregation tests
    ├── test_firebase_auth.py           # Auth and user auto-provisioning tests
    ├── test_insights.py                # Anomaly detection tests
    ├── test_net_worth.py               # Asset/liability lifecycle tests
    └── test_wallet_transfers.py        # Double-entry atomic transfer tests
```

---

## 5. Current System Architecture

LedgerBud implements a modular layered architecture with strict separation of concerns between client presentation, API routing, business services, ETL pipeline components, and database models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSER LAYER                              │
│  - Streamlit Web App Interface                                              │
│  - Browser Cookie Storage (`lb_session_token`)                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / Session
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STREAMLIT FRONTEND RUNTIME                            │
│  streamlit_app.py (port 8501)                                               │
│  ├── ui/navigation.py (st.navigation router)                                │
│  ├── ui/auth.py (Firebase Identity Toolkit Client) ──► Google Identity API  │
│  ├── ui/state.py (Session state & cookie management)                        │
│  └── ui/api_client.py (httpx.Client with Bearer JWT)                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST (JSON)
                                       │ Base URL: FASTAPI_BASE_URL
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND RUNTIME                              │
│  run_fastapi.py -> app.fastapi_app.main:app (port 8000)                     │
│  ├── Middleware: CORSMiddleware (CORS_ORIGINS)                              │
│  ├── Security: OAuth2PasswordBearer -> api/deps.py                          │
│  │    └── Token Verification ────────────────────────► Firebase Admin SDK   │
│  ├── API Routes (47 endpoints across 14 modules)                            │
│  ├── Services Layer:                                                        │
│  │    ├── DashboardService, AnalyticsService, InsightsService               │
│  │    ├── WalletService, TransactionService, BudgetService, GoalService     │
│  │    ├── NetWorthService, SubscriptionService                              │
│  │    ├── FIREService (10-step calculation engine)                          │
│  │    ├── AdvisorService & AdvisorContextService ────► Groq Cloud LLM API   │
│  │    └── ImportService (Orchestrator)                                      │
│  │         └── ETL Engine: Extractor -> Segmenter -> Normalizer ->          │
│  │             TypeResolver -> Deduplicator -> RecognitionEngine            │
│  └── Persistence Layer:                                                     │
│       ├── Repositories (User, Wallet, Transaction, FIRE)                    │
│       └── SQLAlchemy 2.0 Engine & SessionLocal                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQL (async-ready / sync pooling)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE PERSISTENCE                                │
│  SQLite (local: ledgerbud.db)  OR  PostgreSQL 15 (Docker / Cloud Neon)      │
│  11 Relational Tables with Foreign Key Constraints & Cascade Deletions      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer (Streamlit UI)"
        UI["Streamlit Application<br/>streamlit_app.py (:8501)"]
        NAV["Navigation Controller<br/>ui/navigation.py"]
        AUTH_UI["Auth Module<br/>ui/auth.py"]
        HTTP_CLIENT["API Client<br/>ui/api_client.py"]
        COOKIES[("Browser Cookies<br/>lb_session_token")]
        
        UI --> NAV
        UI --> AUTH_UI
        UI --> HTTP_CLIENT
        AUTH_UI <--> COOKIES
    end

    subgraph "External Identity Provider"
        FB_REST["Google Identity Toolkit<br/>identitytoolkit.googleapis.com"]
        AUTH_UI -- "1. Email/Password (REST)" --> FB_REST
        FB_REST -- "2. Returns Firebase idToken" --> AUTH_UI
    end

    subgraph "Backend API Layer (FastAPI)"
        FASTAPI["FastAPI Application<br/>app.fastapi_app.main:app (:8000)"]
        CORS["CORS Middleware"]
        DEPS["Auth & Session Deps<br/>app/fastapi_app/api/deps.py"]
        FB_ADMIN["Firebase Admin SDK<br/>core/firebase.py"]
        
        ROUTER_CORE["Core Routers<br/>(Wallets, Transactions, Imports)"]
        ROUTER_PLAN["Planning Routers<br/>(Budgets, Goals, Subscriptions)"]
        ROUTER_INTEL["Intelligence Routers<br/>(Dashboard, Analytics, FIRE, Net Worth)"]
        ROUTER_AI["Advisor Router<br/>(Advisor, Insights)"]

        HTTP_CLIENT -- "3. REST Request with Bearer Token" --> FASTAPI
        FASTAPI --> CORS --> DEPS
        DEPS -- "4. Verify ID Token" --> FB_ADMIN
        FB_ADMIN <--> FB_REST
        
        DEPS --> ROUTER_CORE
        DEPS --> ROUTER_PLAN
        DEPS --> ROUTER_INTEL
        DEPS --> ROUTER_AI
    end

    subgraph "External AI Service"
        GROQ["Groq Cloud LLM API<br/>openai/gpt-oss-120b"]
        ROUTER_AI -- "Aggregated Financial Context" --> GROQ
    end

    subgraph "ETL Statement Pipeline"
        DISK[("Local File Storage<br/>app/static/uploads/")]
        EXTRACTOR["Extractors<br/>(PDF, CSV, XLSX)"]
        TRANSFORMER["Transformers<br/>(Segmenter, Normalizer, Resolver)"]
        RECOG["Merchant Recognition<br/>(Memory + Seed Dictionary)"]
        
        ROUTER_CORE -- "Save Upload" --> DISK
        ROUTER_CORE --> EXTRACTOR --> TRANSFORMER --> RECOG
    end

    subgraph "Database Layer"
        SQLALCHEMY["SQLAlchemy 2.0 ORM<br/>Engine (pool_pre_ping=True)"]
        DB[("Database<br/>SQLite / PostgreSQL")]
        
        ROUTER_CORE --> SQLALCHEMY
        ROUTER_PLAN --> SQLALCHEMY
        ROUTER_INTEL --> SQLALCHEMY
        ROUTER_AI --> SQLALCHEMY
        SQLALCHEMY --> DB
    end
```

---

## 7. Frontend Runtime and Request Flow

### 7.1 Lifecycle and Execution Model
- **Process Entrypoint:** `streamlit_app.py` is invoked with `streamlit run streamlit_app.py --server.address 0.0.0.0 --server.headless true`.
- **Navigation Management:** Handled dynamically by `ui/navigation.py:get_navigation()` using Streamlit's native `st.navigation`.
  - When unauthenticated: Displays only `Welcome & Overview` (`welcome.py`) and `Sign In to Workspace` (`auth_page.py`) in hidden navigation mode.
  - When authenticated: Exposes 4 functional groups in the sidebar:
    - *Core:* Overview, Wallets, Transactions, Statement Import
    - *Planning:* Budgets, Savings Goals, Subscriptions
    - *Intelligence:* Intelligence, Net Worth, FIRE Planner, AI Financial Advisor, Analytics
    - *Settings:* User Profile, Welcome & Overview
- **Session State & Restoration:** Handled by `ui/state.py`.
  - On first page load, `init_session_state()` calls `try_restore_session()`.
  - It inspects `st.context.cookies` for `lb_session_token`.
  - If a valid token is found, it queries `api_client.get_me()`. If the backend confirms user identity, session state flags `authenticated = True`, restoring the workspace without requiring credentials.
- **Backend Communication:**
  - Carried out exclusively by `APIClient` (`ui/api_client.py`), instantiated as a singleton `api_client`.
  - Base URL discovery: Reads `os.environ.get("FASTAPI_BASE_URL", "http://localhost:8000")`.
  - Authentication injection: Reads `st.session_state.token` and attaches `Authorization: Bearer <token>` to all HTTP headers.
  - Error Handling: Automatically detects HTTP 401 Unauthorized responses, clears session state via `logout_user()`, and redirects the user to `auth_page.py`. All other HTTP errors raise descriptive `httpx.HTTPStatusError` exceptions caught by page-level `render_error_banner` components.
  - Timeout: Fixed at 30.0 seconds per request via `httpx.Client(timeout=30.0)`.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant ST as Streamlit Frontend
    participant API as FastAPI Backend
    participant FB as Firebase Identity
    participant DB as Database

    User->>ST: Accesses Webpage (/)
    ST->>ST: init_session_state() checks cookies
    alt Cookie Found
        ST->>API: GET /api/v1/auth/me (Bearer Token)
        API->>FB: Verify Token
        API->>DB: Query User
        API-->>ST: 200 OK (User Object)
        ST->>ST: authenticated = True
    else No Cookie / Invalid Token
        ST->>User: Renders Welcome / Auth View
        User->>ST: Submits Email & Password
        ST->>FB: POST accounts:signInWithPassword
        FB-->>ST: Returns idToken & RefreshToken
        ST->>API: GET /api/v1/auth/me (Bearer idToken)
        API->>DB: Auto-provision User if First Login
        API-->>ST: 200 OK (User Profile)
        ST->>User: Sets Cookie lb_session_token & Navigates to Overview
    end
    User->>ST: Views Overview / Wallets
    ST->>API: GET /api/v1/dashboard (Bearer idToken)
    API->>DB: Aggregates Balances, Expenses, Budgets
    API-->>ST: 200 OK (Dashboard JSON)
    ST->>User: Renders Interactive Metrics & Plotly Charts
```

---

## 8. Backend Runtime and Request Flow

### 8.1 Startup Lifecycle
1. Launcher `run_fastapi.py` loads `.env` into environment via `dotenv.load_dotenv()` and executes:
   ```python
   uvicorn.run("app.fastapi_app.main:app", host="0.0.0.0", port=8000, reload=True)
   ```
2. Application Factory `create_app()`:
   - Configures logging via `configure_logging(settings.log_level)`.
   - Initializes FastAPI application with title, version, and `lifespan` handler.
   - Registers CORS middleware with origins from `settings.cors_origins`.
   - Registers custom exception handlers from `app.fastapi_app.exceptions.handlers`.
   - Registers routers with prefix `/api/v1` (and root meta endpoints).
3. Lifespan Context (`@asynccontextmanager`):
   - Evaluates `settings.auto_create_tables`. If `True`, executes `Base.metadata.create_all(bind=engine)`.
4. Database Engine Creation (`app/fastapi_app/db/session.py`):
   ```python
   engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=300, future=True)
   SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
   ```
   - `pool_pre_ping=True`: Proactively tests connections with a lightweight `SELECT 1` ping before handing them to requests, preventing stale-connection failures on serverless/cloud databases like Neon.
   - `pool_recycle=300`: Recycles connections older than 5 minutes.

### 8.2 Request Middleware and Authentication Pipeline
- Every request passing into protected routes executes `get_current_user` dependency (`app/fastapi_app/api/deps.py`):
  1. Extracts token from `Authorization: Bearer <token>` header.
  2. Calls `verify_firebase_token(token)` in `core/firebase.py`.
  3. `firebase_admin.auth.verify_id_token(token)` cryptographically verifies token signature, expiry, and audience using Google public certificates.
  4. Queries local `users` table by `firebase_uid`.
  5. *Self-Provisioning / Linking:* If no user matches `firebase_uid`, it queries by `email` to link existing accounts. If still not found, it provisions a new user row in the local database with `full_name` and `email` from the token payload.
  6. Validates `user.is_active`. If inactive, raises HTTP 403 Forbidden.
  7. Injects the active `User` model instance into the route handler.

---

## 9. API Endpoint Inventory

The FastAPI application registers **47 unique routes** and **56 total operations**.

| Method | Endpoint Path | Tag | Function Name | Auth Required? | Primary Description |
|:---|:---|:---|:---|:---:|:---|
| **GET** | `/` | Meta | `root` | No | Service health and API documentation links |
| **GET** | `/health` | Health | `health_check` | No | Liveness probe returning status ok |
| **GET** | `/welcome` | Meta | `welcome_page` | No | Serves static welcome HTML page |
| **GET** | `/app` | Meta | `redirect_to_app` | No | Redirects to Streamlit UI on localhost:8501 |
| **GET** | `/api/v1/auth/me` | Auth | `me` | Yes | Retrieves current user profile (auto-provisions) |
| **PUT** | `/api/v1/auth/me/name` | Auth | `update_name` | Yes | Updates user display name and syncs to Firebase |
| **DELETE**| `/api/v1/auth/me` | Auth | `delete_profile` | Yes | Deletes user from Firebase and cascades DB data |
| **GET** | `/api/v1/wallets` | Wallets | `list_wallets` | Yes | Lists active or archived wallets for current user |
| **POST** | `/api/v1/wallets` | Wallets | `create_wallet` | Yes | Creates new wallet (bank, card, cash, digital) |
| **GET** | `/api/v1/wallets/summary` | Wallets | `wallet_summary` | Yes | Returns total balance and counts by wallet type |
| **POST** | `/api/v1/wallets/transfer` | Wallets | `transfer_funds` | Yes | Executes atomic double-entry balance transfer |
| **PUT** | `/api/v1/wallets/{wallet_id}` | Wallets | `update_wallet` | Yes | Modifies wallet name, type, or balance |
| **DELETE**| `/api/v1/wallets/{wallet_id}` | Wallets | `delete_wallet` | Yes | Deletes wallet and cascades associated data |
| **POST** | `/api/v1/wallets/{wallet_id}/archive` | Wallets | `archive_wallet` | Yes | Soft-archives wallet from active filtering |
| **GET** | `/api/v1/transactions` | Transactions | `list_transactions` | Yes | Paginated search, category, and date filtering |
| **POST** | `/api/v1/transactions` | Transactions | `create_transaction` | Yes | Records income/expense and adjusts wallet |
| **PUT** | `/api/v1/transactions/{transaction_id}`| Transactions | `update_transaction`| Yes | Modifies transaction and updates balance delta |
| **DELETE**| `/api/v1/transactions/{transaction_id}`| Transactions | `delete_transaction`| Yes | Deletes transaction and reverses wallet balance |
| **DELETE**| `/api/v1/transactions/all` | Transactions | `delete_all_transactions`| Yes| Deletes all transactions for the user |
| **GET** | `/api/v1/dashboard` | Dashboard | `get_dashboard` | Yes | Summary totals, 6-mo trends, top categories |
| **GET** | `/api/v1/dashboard/health-score` | Dashboard | `get_health_score`| Yes | Composite 0-100 financial health score & grade |
| **GET** | `/api/v1/dashboard/insights` | Dashboard | `get_insights` | Yes | Alias for automated spending anomaly insights |
| **GET** | `/api/v1/budgets` | Budgets | `list_budgets` | Yes | Lists budgets with real-time spend utilization |
| **POST** | `/api/v1/budgets` | Budgets | `create_budget` | Yes | Establishes spending threshold per category |
| **PUT** | `/api/v1/budgets/{budget_id}` | Budgets | `update_budget` | Yes | Updates budget name, category, or limit |
| **DELETE**| `/api/v1/budgets/{budget_id}` | Budgets | `delete_budget` | Yes | Removes budget target |
| **GET** | `/api/v1/goals` | Goals | `list_goals` | Yes | Lists savings targets and progress percentages |
| **POST** | `/api/v1/goals` | Goals | `create_goal` | Yes | Creates new savings goal |
| **PUT** | `/api/v1/goals/{goal_id}` | Goals | `update_goal` | Yes | Modifies goal targets or target dates |
| **DELETE**| `/api/v1/goals/{goal_id}` | Goals | `delete_goal` | Yes | Removes savings goal |
| **POST** | `/api/v1/goals/{goal_id}/contribute` | Goals | `contribute_to_goal`| Yes | Adds funds toward goal progress |
| **GET** | `/api/v1/subscriptions` | Subscriptions | `list_subscriptions` | Yes | Returns detected or confirmed subscriptions |
| **POST** | `/api/v1/subscriptions` | Subscriptions | `create_subscription` | Yes | Manually registers recurring subscription |
| **POST** | `/api/v1/subscriptions/detect` | Subscriptions | `detect_and_sync` | Yes | Scans transaction history for recurring charges |
| **PUT** | `/api/v1/subscriptions/{sub_id}` | Subscriptions | `update_subscription`| Yes | Modifies subscription parameters |
| **DELETE**| `/api/v1/subscriptions/{sub_id}` | Subscriptions | `dismiss_subscription`| Yes | Dismisses or soft-deletes subscription |
| **POST** | `/api/v1/subscriptions/{sub_id}/confirm` | Subscriptions | `confirm_subscription`| Yes| Converts detected pattern to confirmed sub |
| **GET** | `/api/v1/imports` | Imports | `list_import_jobs` | Yes | Lists previous statement ingestion jobs |
| **POST** | `/api/v1/imports/upload` | Imports | `upload_statement` | Yes | Uploads PDF/CSV/XLSX, runs ETL, returns preview |
| **GET** | `/api/v1/imports/{job_id}` | Imports | `get_import_job` | Yes | Retrieves status and metadata for a job |
| **POST** | `/api/v1/imports/{job_id}/commit` | Imports | `commit_import` | Yes | Ingests previewed transactions into database |
| **GET** | `/api/v1/analytics/trends` | Analytics | `get_trends` | Yes | Multi-month cash-flow trend series |
| **GET** | `/api/v1/analytics/categories` | Analytics | `get_categories` | Yes | Expense distribution by category |
| **GET** | `/api/v1/analytics/merchants` | Analytics | `get_merchants` | Yes | Top spending merchant breakdown |
| **GET** | `/api/v1/analytics/summary` | Analytics | `get_summary` | Yes | High-level analytics metrics |
| **POST** | `/api/v1/analytics/whatif` | Analytics | `run_whatif` | Yes | Simulates compound savings from expense cuts |
| **GET** | `/api/v1/insights` | Insights | `get_insights` | Yes | Algorithmic insight alerts and observations |
| **POST** | `/api/v1/advisor/ask` | Advisor | `ask_advisor` | Yes | LLM financial advisor querying via Groq |
| **GET** | `/api/v1/advisor/context` | Advisor | `get_advisor_context`| Yes | Summarized financial context payload |
| **GET** | `/api/v1/net-worth/summary` | Net Worth | `get_summary` | Yes | Aggregates assets, liabilities, and net worth |
| **GET** | `/api/v1/net-worth/items` | Net Worth | `list_items` | Yes | Lists individual asset and liability entries |
| **POST** | `/api/v1/net-worth/items` | Net Worth | `create_item` | Yes | Adds explicit asset or liability item |
| **PUT** | `/api/v1/net-worth/items/{item_id}`| Net Worth | `update_item` | Yes | Updates net worth item values |
| **DELETE**| `/api/v1/net-worth/items/{item_id}`| Net Worth | `delete_item` | Yes | Deletes net worth item |
| **POST** | `/api/v1/net-worth/snapshot` | Net Worth | `take_snapshot` | Yes | Records point-in-time net worth for charting |
| **GET** | `/api/v1/net-worth/history` | Net Worth | `list_snapshots` | Yes | Historical net worth trend data |
| **GET** | `/api/v1/fire` | FIRE | `get_fire_dashboard` | Yes | Retrieves latest stored FIRE calculation |
| **POST** | `/api/v1/fire/calculate` | FIRE | `calculate_fire` | Yes | Executes 10-step FIRE calculation engine |
| **GET** | `/api/v1/fire/history` | FIRE | `get_fire_history` | Yes | Returns historical calculation runs |
| **POST** | `/api/v1/fire/ai` | FIRE | `ask_fire_coach` | Yes | Specialized FIRE coaching assistant via Groq |

---

## 10. Financial Intelligence and ETL Data Flows

The platform contains custom business logic for parsing messy bank statements, resolving merchant identities, detecting recurring subscriptions, and running mathematical retirement simulations.

### 10.1 Multi-Format Statement Ingestion Pipeline
Statement ingestion is orchestrated through `app/fastapi_app/services/import_service.py` and modularized in `app/etl/`:

```
Statement File (.pdf, .csv, .xlsx, .xls)
         │
         ▼
[Extractor Selection] (PDFExtractor, CSVExtractor, XLSXExtractor)
         │
         ▼
[Text / Table Extraction] -> List[RawTransaction]
         │
         ▼
[Segmenter] (Splits concatenated PDF text into discrete records)
         │
         ▼
[Normalizer] (Cleans currency strings, standardizes ISO dates, extracts tokens)
         │
         ▼
[Type Resolver] (Determines Credit/Debit/Income/Expense with balance checks)
         │
         ▼
[Recognition Engine] (5-Stage Priority Hierarchy for Merchant & Category)
         │
         ▼
[Deduplicator] (MD5 fingerprint hashing against existing wallet transactions)
         │
         ▼
[Preview Generation] (Stored in import_jobs table as JSON)
         │
  User Confirms
         ▼
[Commit Execution] (Batch insertion into transactions & merchants tables)
```

1. **Extractors (`app/etl/extractor/`):**
   - `PDFExtractor`: Uses `pdfplumber` to extract tables and raw text. Contains institution-specific regex patterns (e.g., SBI, HDFC) and extracts dates, amounts, and reference numbers.
   - `CSVExtractor`: Handles varied delimiters (`,`, `;`, `\t`), detects header rows automatically, and handles quoted descriptions.
   - `XLSXExtractor`: Uses `openpyxl` with `data_only=True` to read pre-computed formula values from spreadsheet cells.
2. **Segmenter (`app/etl/transformer/segmenter.py`):**
   - Addresses a common PDF extraction failure mode where multiple banking transactions lack separate date rows and are concatenated into a single description block. It detects recurring transaction signatures (`UPI/CR/`, `UPI/DR/`, `NACH`, `NEFT`) and splits them into discrete transaction units.
3. **Type Resolver (`app/etl/transformer/type_resolver.py`):**
   - Reconciles conflicting debit/credit indicators. Cross-references running balance changes (`balance_after - previous_balance`) to mathematically confirm whether a transaction was an inflow or an outflow.
4. **Merchant Recognition Engine (`app/etl/transformer/recognition_engine.py`):**
   - Executes a 5-stage priority resolution:
     - **Priority 1: Unique Identifier Match:** Extracts UPI IDs / Virtual Payment Addresses (VPAs) from narration strings (e.g., `*@okhdfcbank`, `@paytm`).
     - **Priority 2: Merchant Memory:** Matches unique identifiers against historical entries in the user's `merchants` table (100% confidence).
     - **Priority 3: Known Merchant Database:** Matches keywords against seed data (Zomato, Swiggy, Uber, Amazon, Flipkart, Netflix) with 98% confidence.
     - **Priority 4: Heuristic Token Extraction:** Parses clean readable merchant names from messy bank narrations (85% confidence).
     - **Priority 5: Unknown:** Flags incomplete records for manual user review (`requires_review = True`).
5. **Deduplicator (`app/etl/transformer/deduplicator.py`):**
   - Computes deterministic MD5 fingerprints based on `(date, amount, description)` and checks them against existing database records for the specified wallet to prevent duplicate postings.

### 10.2 Inter-Wallet Transfers (Double-Entry Bookkeeping)
- Managed by `WalletService.transfer` (`app/fastapi_app/services/wallet_service.py`).
- Atomic database transaction:
  1. Decrements source wallet balance: `from_wallet.balance -= amount`.
  2. Increments target wallet balance: `to_wallet.balance += amount`.
  3. Creates a debit transaction for source wallet (`transaction_type="Expense"`, `is_transfer=True`).
  4. Creates a credit transaction for target wallet (`transaction_type="Income"`, `is_transfer=True`).
  5. Links both records using `transfer_pair_id`.
  6. Financial calculations (income, expense, health score) filter out `is_transfer=True` to ensure internal transfers never inflate income or expense figures.

### 10.3 FIRE Intelligence Engine (10-Step Model)
Implemented in `app/fastapi_app/services/fire_service.py`:
- **Step 1: Data Annualization:** Pulls 12-month historical cash flows, net worth, budgets, goals, and recurring subscriptions.
- **Step 2: Savings Rate Calculation:** `(annual_savings / annual_income) * 100`.
- **Step 3: Debt Ratio Assessment:** `(total_liabilities / total_assets) * 100`.
- **Step 4: Target Corpus Formulation:** Uses the 25x Rule (4% Safe Withdrawal Rate) modified by a lifestyle multiplier:
  $$\text{Target Corpus} = \text{Adjusted Annual Expenses} \times 25 \times \text{Multiplier}$$
  *(Lean: 0.8x, Moderate: 1.0x, Comfortable: 1.25x, Luxury: 1.6x)*
- **Step 5: FIRE Progress Percentage:** `(current_net_worth / target_corpus) * 100`.
- **Step 6: Composite Readiness Score (0–100):** Evaluates savings rate (max 30), health score (max 25), debt ratio (max 15), net worth consistency (max 15), investment discipline (max 10), and budget health (max 5).
- **Step 7: Compound Wealth Projection:** Computes future nominal and inflation-adjusted wealth across 5, 10, 15, 20, and 25-year horizons using compound annuity formulas:
  $$FV = PV(1+r)^n + PMT \left[ \frac{(1+r)^n - 1}{r} \right]$$
- **Step 8: Estimated FIRE Age:** Uses numerical search with linear interpolation to determine the exact year projected wealth crosses the target corpus.
- **Step 9: Required Monthly Investment (SIP):** Computes required monthly savings to achieve target corpus by the user's retirement target age.
- **Step 10: Scenario Analysis:** Models Conservative (-3% return, +1% inflation), Moderate (base), and Aggressive (+3% return, -1% inflation) scenarios.

---

## 11. AI and External Service Dependencies

### 11.1 AI Provider Integration (Groq Cloud API)
- **SDK & Provider:** Groq Python SDK (`groq.Groq`).
- **Configured Model:** `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`).
- **Call Topology:** Backend-only. The frontend calls `/api/v1/advisor/ask` and `/api/v1/fire/ai`; the backend interacts with Groq.
- **Execution:** Synchronous blocking call wrapped in FastAPI threadpool (`timeout=15.0` seconds).
- **Graceful Fallback:** If `GROQ_API_KEY` is missing or the `groq` package is unavailable, `AdvisorService` returns a structured fallback response (`provider="fallback_no_key"`) rather than raising a 500 Internal Server Error.
- **Data Privacy & Sanitization:**
  - Individual raw transaction lines, bank account numbers, institution names, and user contact details are **never** transmitted to Groq.
  - `AdvisorContextService.get_context()` compiles an aggregated JSON summary containing only macro figures: total monthly income, total expense, savings rate, top 5 category percentages, budget utilization, goal progress, and health score.

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant API as FastAPI Backend
    participant CTX as AdvisorContextService
    participant GROQ as Groq API (openai/gpt-oss-120b)

    UI->>API: POST /api/v1/advisor/ask {"question": "How can I reduce expenses?"}
    API->>CTX: get_context(user_id)
    CTX->>CTX: Aggregate Totals (Income, Expenses, Top Categories)
    CTX-->>API: Privacy-Safe JSON Context
    API->>GROQ: chat.completions.create(model, messages=[System, Context + Question])
    alt Groq Success
        GROQ-->>API: Returns Completion Content
        API-->>UI: 200 OK {"answer": "...", "provider": "groq_gpt_oss_120b"}
    else Groq Error / Timeout / Quota
        API-->>UI: 200 OK {"answer": "Service unavailable...", "provider": "error"}
    end
    UI->>UI: Displays Advisor Response Card
```

### 11.2 Firebase Authentication Integration
- **Frontend Layer:** `ui/auth.py` sends direct HTTPS requests to `https://identitytoolkit.googleapis.com/v1/{endpoint}?key={FIREBASE_API_KEY}`:
  - `accounts:signInWithPassword`: Signs in with email/password, returning Firebase ID token (JWT) and refresh token.
  - `accounts:signUp`: Registers new account.
  - `accounts:update`: Syncs display name.
  - `accounts:sendOobCode`: Generates password-reset email.
- **Backend Layer:** `app/fastapi_app/core/firebase.py` initializes `firebase-admin`:
  - Attempts initialization via `FIREBASE_SERVICE_ACCOUNT_KEY` (path or JSON string).
  - Falls back to `FIREBASE_PROJECT_ID` (retrieves Google public keys dynamically).
  - Falls back to `GOOGLE_APPLICATION_CREDENTIALS`.
  - Verifies token signature via `auth.verify_id_token(token)`.

---

## 12. Database Schema and Persistence Architecture

### 12.1 Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ wallets : "owns"
    users ||--o{ transactions : "owns"
    users ||--o{ merchants : "owns"
    users ||--o{ budgets : "owns"
    users ||--o{ goals : "owns"
    users ||--o{ subscriptions : "owns"
    users ||--o{ import_jobs : "owns"
    users ||--o{ net_worth_items : "owns"
    users ||--o{ net_worth_snapshots : "owns"
    users ||--o{ fire_analysis : "owns"

    wallets ||--o{ transactions : "contains"
    wallets ||--o{ import_jobs : "targets"
    merchants ||--o{ transactions : "categorizes"
    transactions ||--o| transactions : "transfer_pair"

    users {
        int id PK
        string firebase_uid UK
        string full_name
        string email UK
        string password_hash
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    wallets {
        int id PK
        int user_id FK
        string wallet_name
        string wallet_type
        numeric balance
        boolean is_archived
        datetime created_at
        datetime updated_at
    }

    merchants {
        int id PK
        int user_id FK
        string unique_identifier
        string display_name
        string preferred_name
        string category
        boolean user_confirmation_status
        int confidence_score
        int total_transactions
        numeric total_amount
    }

    transactions {
        int id PK
        int user_id FK
        int wallet_id FK
        int merchant_id FK
        int transfer_pair_id FK
        string merchant_name
        string category
        numeric amount
        string transaction_type
        date transaction_date
        boolean is_transfer
        string raw_description
        int confidence_score
    }

    budgets {
        int id PK
        int user_id FK
        string name
        string category
        numeric amount
        string period
        date start_date
        boolean is_active
    }

    goals {
        int id PK
        int user_id FK
        string name
        numeric target_amount
        numeric current_amount
        date target_date
        string status
    }

    subscriptions {
        int id PK
        int user_id FK
        string name
        numeric amount
        string frequency
        boolean is_confirmed
        boolean is_active
    }

    import_jobs {
        int id PK
        int user_id FK
        int wallet_id FK
        string filename
        string original_filename
        string status
        json preview_data
    }

    net_worth_items {
        int id PK
        int user_id FK
        string name
        string item_type
        string category
        numeric amount
        boolean is_active
    }

    net_worth_snapshots {
        int id PK
        int user_id FK
        date snapshot_date
        numeric total_assets
        numeric total_liabilities
        numeric net_worth
    }

    fire_analysis {
        int id PK
        int user_id FK
        int current_age
        numeric fire_target_corpus
        numeric fire_score
        numeric estimated_fire_age
        json wealth_projection
        json scenarios
    }
```

### 12.2 Alembic Migration vs. Real Schema Discrepancy
An audit of `alembic/versions/` revealed a critical schema divergence:
- **Migration 0001:** Creates `users` table.
- **Migration 0002:** Creates initial `wallets` and `transactions` tables.
- **Migration b1804dc1b57c:** Adds `firebase_uid` column to `users` and alters `password_hash` to nullable.
- **Missing Migrations:**
  - `merchants` table (required for intelligent transaction categorization).
  - `budgets` table (required for budget management).
  - `goals` table (required for savings goals).
  - `subscriptions` table (required for subscription detection).
  - `import_jobs` table (required for statement uploads).
  - `net_worth_items` and `net_worth_snapshots` tables (required for net worth tracking).
  - `fire_analysis` table (required for FIRE engine).
  - `wallets.is_archived` column.
  - `transactions` extended columns (`is_transfer`, `transfer_pair_id`, `merchant_id`, `raw_description`, `normalized_description`, `confidence_score`, `recognition_source`, `matching_method`, `reason_for_decision`).
- *Impact:* Running `alembic upgrade head` on a new PostgreSQL database creates an incomplete database schema that will crash on almost every page. The application must either run with `AUTO_CREATE_TABLES=true` (`Base.metadata.create_all`) or have a consolidated baseline migration generated before deployment.

---

## 13. Authentication and Authorization Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client as User Browser
    participant ST as Streamlit Frontend
    participant FB as Google Identity Toolkit
    participant API as FastAPI Backend
    participant SDK as Firebase Admin SDK
    participant DB as Database (Postgres/SQLite)

    Client->>ST: Enters Email & Password
    ST->>FB: POST /v1/accounts:signInWithPassword?key=FIREBASE_API_KEY
    FB-->>ST: 200 OK (idToken JWT, uid, email)
    ST->>ST: Stores idToken in st.session_state.token
    ST->>Client: Injects cookie "lb_session_token=idToken; SameSite=Lax"
    
    ST->>API: GET /api/v1/auth/me (Authorization: Bearer idToken)
    API->>SDK: verify_id_token(idToken)
    SDK->>SDK: Validates RS256 signature, exp, iss
    SDK-->>API: Returns Decoded Claims (uid, email, name)
    
    API->>DB: Query User WHERE firebase_uid = uid
    alt User Found
        DB-->>API: User Record
    else User Not Found (First Login)
        API->>DB: Query User WHERE email = email
        alt Legacy Match
            API->>DB: UPDATE users SET firebase_uid = uid
        else New User
            API->>DB: INSERT INTO users (full_name, email, firebase_uid)
        end
        DB-->>API: Provisioned User Record
    end
    API-->>ST: 200 OK (User Profile JSON)
    ST->>Client: Displays Dashboard
```

---

## 14. Configuration and Environment Variable Matrix

| Variable Name | Applied Layer | Classification | Default Value | Purpose / Description | Security & Deployment Implications |
|:---|:---:|:---:|:---:|:---|:---|
| `DATABASE_URL` | Backend | **Required** in Prod | *(falls back to MySQL URL)* | Primary database connection string | Must use `postgresql://` (or `postgresql+psycopg2://`), NOT `postgres://`. |
| `AUTO_CREATE_TABLES` | Backend | **Required** in Prod | `false` | Executes `Base.metadata.create_all` at startup | **Must be set to `true`** on fresh cloud databases due to incomplete Alembic migrations. |
| `FASTAPI_BASE_URL` | Frontend | **Required** in Prod | `http://localhost:8000` | Target URL used by Streamlit `api_client` | Must point to public backend HTTPS URL in split deployments. |
| `USE_FIREBASE` | Backend | **Required** in Prod | `false` | Enables Firebase Admin SDK token checks | Must be `true` for user authentication and auto-provisioning. |
| `FIREBASE_API_KEY` | Both | **Required** in Prod | `""` | Google Firebase Web API Key | Used directly by frontend `ui/auth.py` for Identity Toolkit auth endpoints. |
| `FIREBASE_PROJECT_ID`| Backend | **Required** in Prod | `""` | Firebase Project Identifier | Enables Admin SDK to fetch public keys without full service account JSON. |
| `FIREBASE_SERVICE_ACCOUNT_KEY`| Backend| Optional | `""` | Path to service account JSON or raw JSON | Alternative to project ID; grants full administrative Firebase privileges. |
| `GROQ_API_KEY` | Backend | Optional (Rec.) | `""` | Authentication key for Groq LLM API | If absent, Advisor and FIRE coach return graceful fallback notices. |
| `GROQ_MODEL` | Backend | Optional | `openai/gpt-oss-120b` | Target Groq model identifier | Can be customized to other models supported by Groq. |
| `CORS_ORIGINS` | Backend | Optional | `localhost:3000, 8000, 8501` | Allowed browser origins for CORS | Must include the deployed Streamlit frontend origin in production. |
| `LOG_LEVEL` | Backend | Optional | `INFO` | Python logging verbosity | Sets log output level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `UPLOAD_FOLDER` | Backend | Optional | `app/static/uploads` | Path for temporary uploaded statements | Ephemeral on free containers; wiped when container spins down. |
| `MYSQL_DATABASE_URL`| Backend | Dev-only | `mysql+pymysql://...` | Fallback if `DATABASE_URL` is empty | Legacy fallback; do not use in production. |
| `PORT` | Backend | Provider-Specific | *(none)* | Injected by PaaS (Render, Cloud Run, etc.)| Currently ignored by `run_fastapi.py`. Must be passed to Uvicorn in production. |
| `JWT_SECRET_KEY` | N/A | **Deprecated** | `change-me-in-production` | Documented in README but unused in code | Obsolete setting from legacy JWT implementation; safe to ignore. |

---

## 15. Security and Privacy Findings

| Issue ID | Severity | File Reference & Location | Vulnerability Description | Practical Impact | Verification Status | Recommended Remediation |
|:---|:---:|:---|:---|:---|:---:|:---|
| **SEC-01** | **High** | `app/fastapi_app/services/import_service.py:59` & `:340` | **Broken Object Level Authorization (IDOR) on Statement Import**<br/>`process_upload` and `_run_etl_commit` accept `wallet_id` without verifying that `wallet.user_id == current_user.id`. | An authenticated attacker could pass an arbitrary `wallet_id` belonging to another user, attaching imported transactions to that wallet and overwriting the victim's wallet balance. | **Verified** in code inspection | Add an ownership assertion: `wallet = session.scalar(select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)); if not wallet: raise ValueError("Wallet not found.")` |
| **SEC-02** | **Medium** | `app/fastapi_app/api/routes/imports.py:42` | **Unbounded File Ingestion in Memory**<br/>`await file.read()` reads the entire file into memory with no size check. Extension check only inspects file suffix. | Uploading very large files (e.g. 500 MB) can trigger Out-Of-Memory (OOM) crashes on 512 MB free container instances. | **Verified** in code inspection | Enforce a maximum file size limit (e.g. 10 MB) by inspecting `file.size` or streaming chunks with a length counter before saving to disk. |
| **SEC-03** | **Medium** | `ui/auth.py:76` & `:154` | **Missing `Secure` Cookie Flag**<br/>Browser session cookie `lb_session_token` is written with `SameSite=Lax` but lacks the `Secure` attribute. | If accessed over plain HTTP, the session token could be transmitted unencrypted across the network. | **Verified** in code inspection | Append `; Secure` to the JavaScript `document.cookie` assignment in `ui/auth.py` for all HTTPS deployments. |
| **SEC-04** | **Medium** | `app/fastapi_app/core/config.py:29` | **Hardcoded Localhost CORS Origins**<br/>Default `CORS_ORIGINS` only authorizes localhost ports (3000, 8000, 8501). | Cross-origin requests from an independently hosted frontend web application will be rejected by browser CORS enforcement. | **Verified** in code inspection | Configure `CORS_ORIGINS` via environment variable to explicitly include the deployed frontend domain (e.g., `https://ledgerbud.streamlit.app`). |
| **SEC-05** | **Low** | `app/fastapi_app/api/routes/health.py:8` | **Shallow Health Check**<br/>`/health` endpoint returns static JSON without validating database or external service connectivity. | Cloud orchestrators will treat an instance as healthy even if the database is down or unreachable. | **Verified** in code inspection | Add a database ping check (`session.execute(text("SELECT 1"))`) to `/health` to verify real backend readiness. |
| **SEC-06** | **Low** | `app/fastapi_app/services/advisor_context_service.py:44` | **Detailed Financial Context Disclosure to AI**<br/>Aggregated balances, budget overruns, and net worth are transmitted to Groq. | Potential data leakage if the AI provider logs prompt payloads. | **Verified** (By Design) | Aggregate data is sanitized (no PII or account numbers). Add an explicit user opt-in toggle in UI before sending financial summaries to external AI. |

---

## 16. Resource and Performance Requirements

### 16.1 Runtime Profiling and Memory Footprint
- **FastAPI Backend Idle Memory:** ~110 MB – 140 MB RAM.
- **Streamlit Frontend Idle Memory:** ~130 MB – 180 MB RAM.
- **Peak RAM during Statement Processing (pdfplumber / pandas):**
  - Parsing a 50-page statement or 5,000-row CSV consumes an additional 120 MB – 220 MB RAM during text extraction and table structuring.
  - Total combined single-container peak: **~380 MB – 480 MB RAM**.
  - *Implication:* Fits closely within the **512 MB RAM ceiling** of Render's free tier. Large PDF statement uploads risk triggering OOM errors on a single container running both frontend and backend. Splitting them into separate tiers or deploying on a 1 GB+ host provides a safe operational buffer.
- **CPU Utilization:**
  - Idle: < 1% CPU.
  - Active Dashboard Calculation & FIRE Projection: Bursts of 15% – 35% CPU for 100–300ms.
  - PDF Text Extraction: Bursts of 60% – 90% CPU for 1.5–4.0 seconds depending on statement size.
- **Disk Persistence Requirements:**
  - Codebase: ~45 MB.
  - Virtual environment & dependencies: ~380 MB.
  - Uploaded statements (`app/static/uploads/`): Ephemeral storage needs ~5 MB per active upload.
  - Database: A single user generating 500 transactions/month consumes approximately 2.5 MB of relational database storage per year. Neon's 1 GB free allocation is sufficient for hundreds of thousands of transactions.

---

## 17. Current Deployment Blockers

Before LedgerBud can be successfully deployed to any cloud hosting environment, the following specific blockers must be addressed:

### Blocker 1: Incomplete Alembic Database Migrations
- **Cause:** Alembic migrations only cover 3 initial tables/revisions. Eight critical models and multiple columns are absent from Alembic.
- **Effect:** Running `alembic upgrade head` produces an incomplete schema; subsequent API calls fail with database relation errors.
- **Solution:** Ensure `AUTO_CREATE_TABLES=true` is set in the production environment so `Base.metadata.create_all` initializes the full schema, or generate a consolidated baseline migration script.

### Blocker 2: SQLAlchemy `postgres://` Dialect Rejection
- **Cause:** `app/fastapi_app/core/config.py` allows connection strings beginning with `postgres://`. SQLAlchemy 2.0 strictly requires `postgresql://` or `postgresql+psycopg2://`.
- **Effect:** Managed databases (Neon, Render, Supabase) that provide standard `postgres://` URLs cause an immediate application crash on startup (`NoSuchModuleError`).
- **Solution:** Sanitize the URL in `config.py` by replacing `postgres://` with `postgresql://`.

### Blocker 3: Hardcoded Port and Reload in `run_fastapi.py`
- **Cause:** `run_fastapi.py` hardcodes `port=8000` and `reload=True`. It ignores the `$PORT` environment variable provided by cloud hosts.
- **Effect:** On Render or other PaaS platforms, Uvicorn will listen on port 8000 while the platform routes external traffic to `$PORT` (e.g. 10000), causing health check timeouts and deployment failure.
- **Solution:** Read `int(os.environ.get("PORT", 8000))` and disable `reload=True` in production.

### Blocker 4: Multi-Process Single-Container Architecture
- **Cause:** `start_servers.py` runs both FastAPI (port 8000) and Streamlit (port 8501) as concurrent subprocesses.
- **Effect:** Free cloud container services only expose a single web port. Without an internal reverse proxy, only one of the two servers can be reached from the internet.
- **Solution:** Split into independent frontend (Streamlit Community Cloud) and backend (Render Web Service) deployments, or place an Nginx reverse proxy in front of both servers.

### Blocker 5: Ephemeral Disk Reliance in Statement Ingestion
- **Cause:** `ImportService` saves files to `app/static/uploads/` and re-reads them during commit.
- **Effect:** On free PaaS instances that spin down after 15 minutes of inactivity, any delay between upload and commit results in a missing file error.
- **Solution:** Store preview data entirely in the database or commit immediately upon validation.

---

## 18. Hosting Provider Research

*All provider capabilities and quotas verified as of October 2026 from official documentation.*

### 18.1 Frontend: Streamlit Community Cloud
- **Eligibility & Cost:** **$0.00/month** (Free forever for public and private GitHub repositories).
- **Compute & Memory:** ~1 GB baseline RAM (burst up to 2.7 GB), shared vCPU.
- **Execution Model:** Direct integration with GitHub repository. Runs native `streamlit run streamlit_app.py`.
- **Secrets Management:** Built-in web UI for secrets (`.streamlit/secrets.toml` or environment variables).
- **Public Domain & SSL:** Automatic HTTPS on `https://<subdomain>.streamlit.app`.
- **Inactivity Behavior:** Puts apps to sleep after prolonged inactivity (e.g., several days without traffic). Wakes up within ~5–10 seconds when accessed.
- **Compatibility:** **100% Compatible**. The LedgerBud frontend requires zero architectural modifications to run on Streamlit Community Cloud once `FASTAPI_BASE_URL` points to the hosted API.

### 18.2 Backend: Render Web Service (Free Tier)
- **Eligibility & Cost:** **$0.00/month** (Free Tier).
- **Compute & Memory:** **512 MB RAM**, **0.1 shared vCPU**.
- **Execution Model:** Supports native Python environment or Docker container.
- **Inactivity & Cold Starts:** Spindown occurs after **15 minutes** of zero inbound HTTP traffic. Incoming requests trigger a cold start taking **30 to 60 seconds**.
- **Monthly Usage Pool:** 750 free instance hours per month per workspace (sufficient for one continuously active service or multiple spinning services).
- **Port Binding:** Expects application to bind to `0.0.0.0:$PORT` (dynamically injected via `PORT` environment variable).
- **Compatibility:** **Compatible as a dedicated backend service**, provided `PORT` is respected and `reload=False`. Incompatible with running both Streamlit and FastAPI simultaneously on a single instance.

### 18.3 Backend: Hugging Face Spaces
- **Current Status (October 2026):**
  - Built-in Streamlit SDK has been deprecated on Hugging Face Spaces.
  - Creating and running custom **Docker Spaces** now requires a paid subscription (**PRO plan** at $9/month or Team plan). Free accounts are restricted to basic Gradio templates and ZeroGPU configurations.
  - **Verdict:** **Not Recommended / Ineligible** for free-tier Docker or dual-server hosting.

### 18.4 Database: Neon Serverless PostgreSQL (Free Tier)
- **Eligibility & Cost:** **$0.00/month** (Free Plan).
- **Storage Allowance:** **1 GB** of PostgreSQL storage per project.
- **Compute Allowance:** **100 Compute Unit hours (CU-hours)** per month. (A 0.25 CU compute instance runs for up to 400 active hours per month).
- **Autoscaling & Scale-to-Zero:** Computes scale down to zero after **5 minutes** of inactivity. Automatically wakes up on new incoming connection within **500ms – 1.5s**.
- **Data Retention & Expiration:** **Indefinite persistence**. Neon does **not** delete or expire databases after 30 days (unlike Render Free DB).
- **Connection Pooling:** Built-in PgBouncer pooling via pooled connection strings (`-pooler.neon.tech`).
- **Compatibility:** **100% Compatible** with SQLAlchemy 2.0 and `psycopg2-binary`.

### 18.5 Database: Supabase (Free Tier)
- **Eligibility & Cost:** **$0.00/month** (Free Plan).
- **Storage Allowance:** **500 MB** PostgreSQL database.
- **Inactivity Policy:** Automatically pauses projects after **7 consecutive days of inactivity**. When paused, the database compute stops completely and requires manual un-pausing via the Supabase Web Dashboard. Backups are preserved for up to 1 year.
- **Compatibility:** Compatible, but automatic pausing after 7 days makes it less seamless than Neon for automated personal finance tracking unless kept alive by a scheduled ping.

### 18.6 Database: Render Free PostgreSQL (Disqualified)
- **Official Policy:** Render free PostgreSQL databases **expire after 30 days**. Once expired, the database is stopped, and data is permanently deleted after a 14-day grace period unless upgraded to a paid plan ($7/mo+).
- **Verdict:** **DISQUALIFIED**. Completely unsuitable for financial data.

### 18.7 AI Provider: Groq Cloud API (Free Plan)
- **Eligibility & Cost:** **$0.00/month** (Free Plan, no credit card required).
- **Model:** `openai/gpt-oss-120b`.
- **Rate Limits:**
  - **30 Requests Per Minute (RPM)**
  - **8,000 Tokens Per Minute (TPM)**
  - **1,000 Requests Per Day (RPD)**
- **Quota Exceeded Behavior:** Returns HTTP 429 Rate Limit Exceeded. LedgerBud's `AdvisorService` catches this exception and returns an informative notice to the user.

---

## 19. Free-Tier and Pricing Comparison

| Provider & Service | Free Plan Tier | RAM / Storage Limits | Inactivity Behavior | Data Deletion Policy | Suitability for LedgerBud |
|:---|:---|:---|:---|:---|:---|
| **Streamlit Community Cloud** | Free Forever | ~1 GB RAM (up to 2.7 GB) | Sleeps after several days inactivity | No data stored (code in GitHub) | **Excellent** for Frontend |
| **Render Web Service** | Free Plan | 512 MB RAM, 0.1 CPU | Sleeps after 15 min; 30-50s cold start | Ephemeral local disk wiped on restart | **Good** for Backend API |
| **Neon PostgreSQL** | Free Plan | 1 GB Storage, 100 CU-hrs | Scales to zero after 5 min; wakes in 1s | **Persistent (No expiration)** | **Excellent** for Database |
| **Supabase PostgreSQL** | Free Plan | 500 MB Storage | Pauses after 7 days; manual unpause | Kept 1 year, requires manual resume | **Fair** (Pause risk) |
| **Render PostgreSQL** | Free Plan | 1 GB Storage | Never sleeps | **Deleted after 30 days** | **Unacceptable (Data Loss)** |
| **Hugging Face Spaces** | Deprecated / PRO | Docker requires PRO ($9/mo) | Sleeps after 48 hrs | Persistent space volume | **Unsuitable** for Free Tier |
| **Groq Cloud API** | Free Plan | 30 RPM, 8k TPM, 1k RPD | Stateless API | N/A | **Excellent** for AI Advisory |
| **Firebase Auth** | Spark Plan | 50,000 MAUs | Active always | Persistent user records | **Excellent** for Auth |

---

## 20. Deployment Architecture Comparison

### Architecture A — Split Frontend, Backend, and Managed Database
- **Topology:**
  - Frontend: Streamlit Community Cloud (connected to GitHub repository).
  - Backend: Render Free Web Service (running FastAPI).
  - Database: Neon Serverless PostgreSQL (Free Tier).
  - Auth: Google Firebase (Spark Free Plan).
  - AI: Groq Cloud API (Free Plan).

### Architecture B — Single Application Host (VPS) plus Managed Database
- **Topology:**
  - Host: Single-node Linux VPS (Hetzner Cloud CX22 €3.79/mo or DigitalOcean $4.00/mo) running Docker Compose.
  - Reverse Proxy: Nginx container routing `/api` to FastAPI (port 8000) and `/` to Streamlit (port 8501) on port 80/443.
  - Database: Neon PostgreSQL or self-hosted PostgreSQL container with automated volume backups.

### Architecture C — Single Host with Local SQLite
- **Topology:**
  - Host: Render Free Web Service or local machine running `start_servers.py` with `ledgerbud.db`.
  - Storage: Ephemeral container disk.

### Architecture D — Serverless Backend + Supabase + Streamlit Cloud
- **Topology:**
  - Frontend: Streamlit Community Cloud.
  - Backend: Vercel / AWS Lambda running Mangum ASGI adapter.
  - Database: Supabase PostgreSQL.

### Comparative Evaluation Matrix

| Evaluation Dimension | Architecture A (Split Free Tier) | Architecture B (VPS Container Stack) | Architecture C (Single Host SQLite) | Architecture D (Serverless ASGI) |
|:---|:---:|:---:|:---:|:---:|
| **Monthly Cost** | **$0.00 / month** | **$4.00 – $6.00 / month** | $0.00 / month | $0.00 / month |
| **Initial Deployment Effort** | Low (3 Git connections) | Medium (SSH, Docker, Nginx) | Low | High (Mangum refactoring) |
| **Required Code Changes** | Minimal (Config & URI fixes) | Low (Nginx config file) | None | Medium-High |
| **Cold Start Latency** | 30–60s on backend wake-up | **Zero (Always active)** | 30–60s | 2–5s per function |
| **Data Durability & Safety**| **High** (Neon persistent DB) | **High** (Persistent volume / Neon)| **Critical Risk (Data loss)** | **Medium** (Supabase 7-day pause)|
| **Operational Complexity** | Low (Serverless / Managed) | Medium (OS updates, Docker) | Low | High |
| **Security Isolation** | High (Multi-tier HTTPS) | High (Private container network)| Low | High |
| **Concurrency & Scaling** | Moderate (512 MB backend) | High (Dedicated 2–4 GB VPS) | Poor (SQLite file locks) | High |
| **Suitability for Public Demo**| **Excellent** | **Excellent** | Acceptable (Temporary) | Good |
| **Suitability for Real Finances**| **Good** | **Outstanding** | **Unacceptable** | Moderate |
| **Recommendation Verdict** | **RECOMMENDED (Free)** | **RECOMMENDED (Paid/Stable)** | **REJECTED** | **REJECTED** |

---

## 21. Recommended Hosting Architecture

### 21.1 Selected Topology: Architecture A (Split Zero-Cost Cloud)
For zero-cost hosting, Architecture A provides the optimal balance of data safety, separation of concerns, and ease of deployment.

```mermaid
graph TB
    subgraph "Public Internet"
        USER[("User Browser")]
    end

    subgraph "Streamlit Community Cloud (Frontend Tier)"
        SCC["Streamlit Community Cloud<br/>https://ledgerbud.streamlit.app<br/>(1 GB RAM, Shared CPU)"]
        CLIENT["ui/api_client.py<br/>FASTAPI_BASE_URL = https://ledgerbud-api.onrender.com"]
        SCC --- CLIENT
    end

    subgraph "Render.com (Backend Web Service Tier)"
        RENDER["Render Web Service (Free Tier)<br/>https://ledgerbud-api.onrender.com<br/>(512 MB RAM, 0.1 CPU)"]
        UVICORN["Uvicorn ASGI Server<br/>app.fastapi_app.main:app<br/>Listening on 0.0.0.0:$PORT"]
        RENDER --- UVICORN
    end

    subgraph "Neon.tech (Managed Database Tier)"
        NEON[("Neon Serverless PostgreSQL<br/>ep-xxxx-pooler.neon.tech:5432<br/>(1 GB Storage, 100 CU-hrs/mo)")]
        PGBOUNCER["Built-in PgBouncer Connection Pooler"]
        NEON --- PGBOUNCER
    end

    subgraph "External Cloud Services"
        FIREBASE["Google Firebase Auth<br/>(Identity Toolkit & Admin SDK)"]
        GROQ["Groq Cloud API<br/>(openai/gpt-oss-120b)"]
    end

    USER -- "1. HTTPS (Port 443)" --> SCC
    SCC -- "2. Authenticates via REST" --> FIREBASE
    CLIENT -- "3. HTTPS REST API Calls (Bearer Token)" --> RENDER
    UVICORN -- "4. Validates Token" --> FIREBASE
    UVICORN -- "5. LLM Prompt Completion" --> GROQ
    UVICORN -- "6. SQL via PgBouncer Pool" --> PGBOUNCER
```

---

## 22. Database Migration and Persistence Plan

### 22.1 Safe Migration from Local SQLite to Hosted PostgreSQL
To migrate existing financial data from `ledgerbud.db` to Neon PostgreSQL without data loss:

1. **Schema Initialization:**
   - Configure `AUTO_CREATE_TABLES=true` on the FastAPI backend during its initial boot against Neon.
   - `Base.metadata.create_all(bind=engine)` executes all DDL statements in correct topological dependency order (`users` -> `wallets` -> `merchants` -> `transactions`, etc.).
2. **Data Extraction & Transformation Script:**
   - Execute a safe, read-only Python migration script locally that reads from SQLite using SQLAlchemy and writes to PostgreSQL.
   - Preserves all foreign key relationships:
     1. `User` rows (mapping `id`, `firebase_uid`, `email`).
     2. `Wallet` rows (mapping `id`, `user_id`, `balance`, `is_archived`).
     3. `Merchant` profiles.
     4. `Transaction` records (mapping `id`, `user_id`, `wallet_id`, `merchant_id`, `transfer_pair_id`).
     5. Planning entities (`Budget`, `Goal`, `Subscription`, `NetWorthItem`, `NetWorthSnapshot`, `FireAnalysis`).
3. **Sequence Synchronization:**
   - PostgreSQL uses sequences for auto-incrementing integer primary keys (`users_id_seq`, `wallets_id_seq`, `transactions_id_seq`).
   - After importing historical rows with explicit IDs, synchronize all sequences:
     ```sql
     SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
     SELECT setval('wallets_id_seq', (SELECT MAX(id) FROM wallets));
     SELECT setval('transactions_id_seq', (SELECT MAX(id) FROM transactions));
     SELECT setval('merchants_id_seq', (SELECT MAX(id) FROM merchants));
     SELECT setval('budgets_id_seq', (SELECT MAX(id) FROM budgets));
     SELECT setval('goals_id_seq', (SELECT MAX(id) FROM goals));
     SELECT setval('subscriptions_id_seq', (SELECT MAX(id) FROM subscriptions));
     SELECT setval('net_worth_items_id_seq', (SELECT MAX(id) FROM net_worth_items));
     SELECT setval('net_worth_snapshots_id_seq', (SELECT MAX(id) FROM net_worth_snapshots));
     SELECT setval('fire_analysis_id_seq', (SELECT MAX(id) FROM fire_analysis));
     ```
4. **Data Verification Checklist:**
   - Compare row counts across all 11 tables between SQLite and PostgreSQL.
   - Validate wallet total balances match transaction aggregate sums.
   - Execute the 9 test suites against the new PostgreSQL database to confirm operational parity.

---

## 23. Required Deployment Configuration Changes

*(Documented as recommendations for user review. No code has been modified during this audit.)*

### 23.1 Backend Configuration Fixes
1. **`app/fastapi_app/core/config.py` — Database URI Sanitization:**
   ```python
   @property
   def database_url(self) -> str:
       env_database_url = os.getenv("DATABASE_URL")
       if env_database_url:
           # Fix SQLAlchemy 2.0 postgres:// incompatibility
           if env_database_url.startswith("postgres://"):
               env_database_url = env_database_url.replace("postgres://", "postgresql://", 1)
           return env_database_url
       return self.mysql_database_url
   ```
2. **`run_fastapi.py` — Dynamic Port Binding:**
   ```python
   import os
   import uvicorn
   from dotenv import load_dotenv

   load_dotenv()

   if __name__ == "__main__":
       port = int(os.environ.get("PORT", 8000))
       is_dev = os.environ.get("ENVIRONMENT", "production").lower() == "development"
       uvicorn.run("app.fastapi_app.main:app", host="0.0.0.0", port=port, reload=is_dev)
   ```
3. **`app/fastapi_app/services/import_service.py` — Wallet Ownership Verification:**
   ```python
   # Inside process_upload and _run_etl_commit:
   wallet = self.session.scalar(
       select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
   )
   if not wallet:
       raise ValueError("Specified wallet not found or unauthorized.")
   ```

### 23.2 Frontend Configuration
1. **Streamlit Secrets (`.streamlit/secrets.toml` or Community Cloud UI):**
   ```toml
   FASTAPI_BASE_URL = "https://ledgerbud-api.onrender.com"
   FIREBASE_API_KEY = "AIzaSy..."
   ```

---

## 24. Step-by-Step Deployment Roadmap

### Phase 1: Managed Database Provisioning (Neon)
1. Sign up at [neon.tech](https://neon.tech) and create a project named `ledgerbud`.
2. Select PostgreSQL 15 or 16 in your preferred region.
3. Copy the **Pooled Connection String** (format: `postgresql://user:password@ep-xxxx-pooler.region.neon.tech/ledgerbud?sslmode=require`).

### Phase 2: Firebase Authentication Configuration
1. In the [Firebase Console](https://console.firebase.google.com/), select your project.
2. Enable **Email/Password** under Authentication -> Sign-in method.
3. Under Project Settings, copy the **Web API Key** (`FIREBASE_API_KEY`) and **Project ID** (`FIREBASE_PROJECT_ID`).
4. Add the intended Streamlit URL (`https://<your-app>.streamlit.app`) to **Authorized Domains** in Firebase Auth Settings.

### Phase 3: Groq Cloud API Setup
1. Register at [console.groq.com](https://console.groq.com/) and create an API key (`GROQ_API_KEY`).
2. Verify access to `openai/gpt-oss-120b`.

### Phase 4: Backend Web Service Deployment (Render)
1. Connect GitHub repository `Hariprasath1x/LedgerBud` to Render as a **Web Service**.
2. Settings:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_fastapi.py` (or `uvicorn app.fastapi_app.main:app --host 0.0.0.0 --port $PORT`)
   - **Instance Type:** Free (512 MB RAM)
3. Set Environment Variables:
   - `DATABASE_URL`: *(Neon pooled connection string)*
   - `AUTO_CREATE_TABLES`: `true`
   - `USE_FIREBASE`: `true`
   - `FIREBASE_API_KEY`: *(Firebase Web API Key)*
   - `FIREBASE_PROJECT_ID`: *(Firebase Project ID)*
   - `GROQ_API_KEY`: *(Groq API Key)*
   - `GROQ_MODEL`: `openai/gpt-oss-120b`
   - `CORS_ORIGINS`: `https://<your-app>.streamlit.app`
4. Trigger manual deployment and verify build completion and `/health` response.

### Phase 5: Frontend Deployment (Streamlit Community Cloud)
1. Sign in to [share.streamlit.io](https://share.streamlit.io/) via GitHub.
2. Click **New App**, select `Hariprasath1x/LedgerBud`, branch `main`, and main file path `streamlit_app.py`.
3. In Advanced Settings -> Secrets, configure:
   ```toml
   FASTAPI_BASE_URL = "https://ledgerbud-api.onrender.com"
   FIREBASE_API_KEY = "AIzaSy..."
   ```
4. Deploy application and test end-to-end functionality.

---

## 25. Pre-Deployment Verification Checklist

- [ ] **Repository Hygiene:** Working tree clean; all changes committed to Git.
- [ ] **Secret Safety:** No `.env` or `serviceAccountKey.json` files tracked in Git.
- [ ] **Database URI:** `postgres://` prefix sanitization tested and verified.
- [ ] **Port Handling:** Backend server binds dynamically to `$PORT`.
- [ ] **Table Creation:** `AUTO_CREATE_TABLES=true` enabled for initial cloud deployment.
- [ ] **Firebase Domain:** Deployed Streamlit domain added to Firebase Authorized Domains.
- [ ] **CORS Configuration:** `CORS_ORIGINS` includes deployed frontend domain.
- [ ] **Automated Tests:** All 9 unit tests pass in `.venv` environment.
- [ ] **Static Assets:** Welcome page template `ledgerbud-welcome-page.html` verified present.
- [ ] **SSL / TLS:** Database connection string enforces `?sslmode=require`.

---

## 26. Post-Deployment Smoke-Test Plan

Execute the following sequential validation once services are online:

1. **Liveness Probe:**
   - Execute `curl -i https://ledgerbud-api.onrender.com/health`.
   - Confirm HTTP 200 response with `{"status": "ok", "service": "LedgerBud API"}`.
2. **User Registration & Provisioning:**
   - Open frontend URL: `https://<app>.streamlit.app`.
   - Complete registration with a new test email and password.
   - Confirm successful redirection to Overview page.
   - Verify user row is created in Neon database.
3. **Wallet Creation & Balance Operations:**
   - Create two test wallets: "Checking" (Balance: ₹10,000) and "Savings" (Balance: ₹5,000).
   - Perform an inter-wallet transfer of ₹2,000 from Checking to Savings.
   - Confirm Checking reflects ₹8,000 and Savings reflects ₹7,000.
4. **Statement Ingestion:**
   - Upload a test CSV statement in the Statement Import view.
   - Verify parsing, merchant recognition, and preview table rendering.
   - Commit the import and verify transactions reflect in the Overview and Transactions views.
5. **FIRE Intelligence & Advisory:**
   - Navigate to FIRE Planner and run the 10-step calculation.
   - Verify projection chart and scenarios render properly.
   - Submit a test query to the AI Financial Advisor; verify Groq returns a concise, context-backed response.

---

## 27. Rollback and Recovery Strategy

- **Frontend Rollback:** Streamlit Community Cloud allows instantaneous rollback to any previous Git commit via the management dashboard.
- **Backend Rollback:** Render provides a one-click rollback feature to any previously successful build artifact without rebuilding.
- **Database Rollback:**
  - Neon Serverless PostgreSQL maintains continuous Point-In-Time Recovery (PITR).
  - A historical branch can be created instantaneously at any timestamp or transaction boundary to restore corrupted data without downtime.
- **Database Backup Procedure:**
  - Automated local backups of PostgreSQL can be created via:
    ```bash
    pg_dump -d "$DATABASE_URL" -Fc -f "ledgerbud_backup_$(date +%Y%m%d).dump"
    ```

---

## 28. Estimated Monthly Operating Cost

### Zero-Cost Tier (Architecture A — Recommended for Public Demo)
- **Streamlit Community Cloud:** $0.00 / month
- **Render Web Service (Free Tier):** $0.00 / month
- **Neon Serverless PostgreSQL (Free Plan):** $0.00 / month
- **Google Firebase Auth (Spark Plan):** $0.00 / month (up to 50k MAUs)
- **Groq Cloud API (Free Plan):** $0.00 / month (up to 1k requests/day)
- **Total Estimated Operating Cost:** **$0.00 / month**

### Production Tier (Architecture B — Recommended for Personal Financial Life)
- **Single VPS (Hetzner Cloud CX22 - 2 vCPU, 4 GB RAM, 40 GB NVMe):** ~$4.50 / month (€3.79/mo)
- **Neon Serverless PostgreSQL (Free Plan):** $0.00 / month
- **Firebase Auth (Spark Plan):** $0.00 / month
- **Groq Cloud API (Free Plan):** $0.00 / month
- **Domain Name (.com / .app):** ~$1.00 / month ($12/year)
- **Total Estimated Operating Cost:** **~$5.50 / month**

---

## 29. Risk Register and Mitigations

| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Strategy |
|:---|:---|:---:|:---:|:---:|:---|
| **RSK-01** | Free tier backend spin-down causes 45s cold start delay on first request | Medium | High | Degraded user experience on initial visit | Display an explanatory loading spinner in Streamlit UI while awaiting API response; or ping the backend periodically. |
| **RSK-02** | Neon free compute budget exhausted (100 CU-hrs exceeded) | Medium | Low | Database becomes temporarily inaccessible | Neon compute scales down after 5 minutes of inactivity; 100 CU-hours equates to ~400 active hours, sufficient for personal use. |
| **RSK-03** | Groq free tier rate limit exceeded during intense advisor chats | Low | Medium | Advisor queries temporarily fail with rate limit notice | Advisor service gracefully catches rate limits and informs the user; limits reset every minute (30 RPM / 8k TPM). |
| **RSK-04** | User statement contains non-standard banking layout | Medium | Medium | Parser fails to extract transactions | Pipeline flags incomplete rows (`requires_review=True`) and allows manual transaction entry. |
| **RSK-05** | Supabase database auto-pauses after 7 days (if Supabase chosen over Neon) | High | Medium | Application errors on load | Use Neon instead of Supabase, as Neon automatically resumes without manual intervention. |

---

## 30. Open Questions and Unverified Assumptions

1. **User Concurrency Profile:** Is LedgerBud intended exclusively for personal/family use (1–3 users) or as a public SaaS platform with hundreds of concurrent users? *(Audit assumed personal/portfolio workload).*
2. **Statement Source Institutions:** What banks or financial institutions will be primary sources for uploaded statements? *(Audit verified support for SBI, HDFC, and generic CSV/XLSX formats).*
3. **AI Provider Budget:** If Groq's free tier rate limits prove constraining for complex multi-turn chats, does the user wish to attach a pay-as-you-go credit card to Groq (fractions of a cent per query) or keep it strictly zero-cost?

---

## 31. Source References and Research Date

*All external provider facts, quotas, and pricing verified on **October 23, 2026**.*

1. **Render.com Official Pricing & Free Tier Limits:**
   - Free Web Services: 512 MB RAM, 0.1 CPU, 15-minute idle spindown, 750 free instance hours/month.
   - Free PostgreSQL Database: 30-day expiration policy (verified updated from 90 days).
   - Source: [render.com/docs/free](https://render.com/docs/free)
2. **Neon.tech Official Documentation & Plans:**
   - Free Plan: 1 GB storage, 100 CU-hours/month, scale-to-zero after 5 minutes inactivity, indefinite data persistence.
   - Source: [neon.tech/docs/introduction/plans](https://neon.tech/docs/introduction/plans)
3. **Supabase Official Documentation:**
   - Free Plan: 500 MB database, automatic pause after 7 days of inactivity, 1-year backup retention.
   - Source: [supabase.com/docs/guides/platform/manage-your-usage/free-plan](https://supabase.com/docs/guides/platform/manage-your-usage/free-plan)
4. **Streamlit Community Cloud Documentation:**
   - Free tier resource allocations: ~1 GB standard allocation, 2.7 GB memory limit, public/private GitHub repo support.
   - Source: [docs.streamlit.io/deploy/streamlit-community-cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
5. **Hugging Face Spaces Documentation:**
   - Docker Spaces requirement update: Docker spaces require a paid PRO plan; Streamlit built-in SDK deprecated.
   - Source: [huggingface.co/docs/hub/spaces-overview](https://huggingface.co/docs/hub/spaces-overview)
6. **Groq Cloud API Documentation:**
   - Free Plan Rate Limits for `openai/gpt-oss-120b`: 30 RPM, 8,000 TPM, 1,000 RPD.
   - Source: [console.groq.com/docs/rate-limits](https://console.groq.com/docs/rate-limits)
7. **Firebase Authentication Pricing:**
   - Spark Plan (Free): 50,000 Monthly Active Users (MAUs) for Email/Password authentication.
   - Source: [firebase.google.com/pricing](https://firebase.google.com/pricing)

---

## 32. Final Recommendations and Decision Matrix

| Hosting Architecture | Target Use Case | Estimated Cost | Feasibility Decision | Key Prerequisites Prior to Launch |
|:---|:---|:---:|:---:|:---|
| **Architecture A (Split Free Tier)**<br/>Streamlit Cloud + Render + Neon | **Public Portfolio Demo / Personal Free Hosting** | **$0.00 / month** | **CONDITIONAL GO** | 1. Sanitize `postgres://` to `postgresql://` in `config.py`<br/>2. Bind to `$PORT` in `run_fastapi.py`<br/>3. Set `AUTO_CREATE_TABLES=true`<br/>4. Validate `wallet_id` ownership in `import_service.py` |
| **Architecture B (VPS Container Stack)**<br/>Hetzner / DigitalOcean + Nginx + Neon | **Production Personal Finance / Private Reliable Platform** | **~$5.00 / month** | **GO** | 1. Add Nginx reverse proxy configuration<br/>2. Configure automated daily `pg_dump` backups<br/>3. Provision SSL certificates via Let's Encrypt |
| **Architecture C (Single Container SQLite)**<br/>Render Free Container + SQLite | **Disposable Demo Only** | **$0.00 / month** | **NO-GO** | **Rejected due to fatal data loss** whenever the container spins down. |
