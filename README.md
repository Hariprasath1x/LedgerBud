# LedgerBud 📈

**LedgerBud** is a modern, production-ready Financial Intelligence Platform designed to parse statements, auto-categorize spending, track budgets, evaluate financial health, and project future wealth. 

The platform features a **native Streamlit UI dashboard** communicating with a high-performance **FastAPI backend** using SQLAlchemy and JWT authentication. It also supports a legacy **Flask MVC UI** for backward compatibility.

---

## 🏗️ Architecture

LedgerBud operates on a decoupled client-server architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       Streamlit UI                          │
│            (Interactive Dashboard & Charts - 8501)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ (HTTP + JWT Auth)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│               (REST API Services - Port 8000)               │
└──────┬───────────────────────────────────────────────┬──────┘
       │ (ORM / Migrations)                            │ (Ingestion ETL)
       ▼                                               ▼
┌──────────────────────────────┐              ┌────────────────┐
│         SQLAlchemy           │              │  pdfplumber /  │
│         (Database)           │              │  Pandas Engine │
└──────────────┬───────────────┘              └────────────────┘
               ▼
┌──────────────────────────────┐
│   PostgreSQL / MySQL / DB    │
└──────────────────────────────┘
```

---

## 🧩 Core Features

*   **🧠 Groq AI Financial Advisor**: Interactive personal finance advisor powered by Groq and LLaMA 3.1. It generates a privacy-preserving aggregated context of your monthly financials (wallet balances, health score, category totals, net worth, budgets, active goals, and anomalies) without ever sending raw transaction logs to the LLM.
*   **🏦 Net Worth Tracker**: Monitor your absolute net worth by adding and updating custom assets and liabilities. It records point-in-time historical snapshots to visualize long-term wealth trends using interactive Plotly charts.
*   **🔍 Deterministic Insights Engine**: A robust, rule-based engine that automatically highlights financial risks (like zero-income months, category spending spikes exceeding 3-month averages by 150%+, budget utilization over 80%/100%, and drops in MoM savings rate).
*   **💳 Complete Multi-Wallet Management**: Comprehensive management of accounts supporting Bank, Cash, UPI, and Credit card types. Enables archiving accounts safely while preserving transaction logs, and performing atomic transfers between wallets (generating linked income-expense transaction pairs).
*   **📥 Smart Statement Ingestion (ETL) Engine**: Drag-and-drop ingestion of Bank PDF/CSV/XLSX statements (optimized for Indian banks like SBI, HDFC, ICICI, Axis, Canara, etc.). Built on clean ETL principles:
    *   **Extract**: Fast text & table parsing using `pdfplumber` and `pandas`.
    *   **Transform**: Intelligent deduplication, missing value checks, date/currency normalization, and auto-mapping.
    *   **Load**: Transaction persistence with pre-import previews and transparency logs.
*   **🏷️ Merchant Dictionary Engine**: Automatic categorization of noisy transaction strings (e.g., `UPI/SWIGGY` or `SWIGGY ONLINE` mapped to `Swiggy` under the `Food & Dining` category).
*   **📊 Financial Overview & Analytics**: Live visualization of cash flow, wallet balances, and categorical expense distributions via Plotly.
*   **📈 Budget Monitoring**: Create monthly, category-level spending thresholds and track real-time consumption.
*   **🎯 Savings Goals Tracker**: Set target values, track contributions, and project completion dates.
*   **🔄 Subscription & Recurring Payment Detector**: Automatically identify recurring expenses (e.g., Netflix, Spotify) to prevent subscription leakages.
*   **🧠 Intelligence Layer**: Calculate a 0-100 Financial Health Score based on budget discipline, saving rate, and debt-to-income ratio, paired with actionable rule-based advisory insights.
*   **🧮 What-If Compound Interest Calculator**: Simulate the long-term wealth impact (10+ year projections) of reducing minor spending categories.

---

## 🚀 Running LedgerBud Locally (Recommended Stack)

Follow these steps to run the modern Streamlit frontend and FastAPI backend.

### 1. Configure the Environment
Create or edit your `.env` file in the project root:

```env
# Database Connection (MySQL or PostgreSQL)
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/ledgerbud

# Security & JWT Configuration
JWT_SECRET_KEY=ledgerbud-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# FastAPI Configuration
AUTO_CREATE_TABLES=true
FASTAPI_BASE_URL=http://localhost:8000
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI Backend
```bash
python run_fastapi.py
```
*   **Swagger Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs) to view and test backend routes.

### 4. Start the Streamlit Frontend
In a new terminal window:
```bash
streamlit run streamlit_app.py
```
*   **Access the App**: Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Quick Start with Docker (Legacy Flask Stack)

If you prefer to run the legacy Flask MVC interface (Port 5000) or test the application within Docker, use the following compose configuration.

### Prerequisites
*   Docker
*   Docker Compose

### 1. Build and Run Containers
```bash
docker-compose up --build -d
```
This command starts:
1.  A PostgreSQL 15 database instance.
2.  The Flask web server configured to build and seed database tables automatically on launch.

### 2. Access the Application
*   Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

### 3. Tear Down
```bash
docker-compose down
```

---

## 🏗️ Legacy Stack Manual Setup (Flask)

If you wish to run the Flask application directly on your local machine:

### 1. Initialize the Database
Ensure PostgreSQL or MySQL is running, then create a database named `ledgerbud`.
Run the CLI command to initialize tables and seed initial category / merchant dictionary data:
```bash
flask create-db
```
*(Alternatively, run `flask seed` to re-seed category mapping rules).*

### 2. Run the Server
```bash
python run.py
```
or
```bash
flask run --port=5000
```

---

## 📂 Project Structure

```
├── app/
│   ├── etl/               # PDF/CSV statement extraction & transformation engine
│   ├── fastapi_app/       # Modern FastAPI backend (routes, models, schemas, services)
│   ├── intelligence/      # Financial Health Score & Merchant Dictionary engine
│   ├── models/            # Legacy SQLAlchemy Flask models
│   ├── routes/            # Legacy Flask Blueprints & route handlers
│   ├── static/            # Static assets
│   ├── templates/         # Legacy HTML templates
│   ├── seeder.py          # Category & Merchant dictionary database seeds
│   └── extensions.py      # Flask extensions helper
├── ui/                    # Streamlit frontend pages & API components
├── streamlit_app.py       # Main Streamlit app launcher
├── run_fastapi.py         # FastAPI app launcher
├── run.py                 # Flask app launcher
└── docker-compose.yml     # Docker compose file for PostgreSQL and Flask
```

