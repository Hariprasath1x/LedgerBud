# LedgerBud 📈

**LedgerBud** is an AI-powered Personal Finance Intelligence Platform built with Python Flask, SQLAlchemy, PostgreSQL, and a completely custom, sleek Dark Mode UI.

It allows you to automatically extract structured data from Bank PDF Statements, auto-categorize transactions using a smart Merchant Dictionary, detect subscriptions, and view actionable financial insights.

---

## 🚀 Quick Start (Docker)

The easiest way to run LedgerBud is via Docker. This ensures you have both the Flask backend and the required PostgreSQL database running seamlessly without manual setup.

### Prerequisites
- Docker
- Docker Compose

### 1. Build and Run
Clone this repository and run the following command from the root directory:

```bash
docker-compose up --build -d
```

This will:
1. Start a PostgreSQL 15 database instance.
2. Build the Flask application.
3. Automatically initialize the database schemas and seed the initial categories and merchant dictionary.
4. Expose the web application on port `5000`.

### 2. Access the Application
Open your browser and navigate to:
**[http://localhost:5000](http://localhost:5000)**

### 3. Stop the Application
To stop the running containers:
```bash
docker-compose down
```

---

## 🏗️ Manual Setup (Without Docker)

If you prefer to run the application manually on your host machine:

### 1. Install PostgreSQL
Ensure you have PostgreSQL installed and running on `localhost:5432`.
Create a database named `ledgerbud`:
```sql
CREATE DATABASE ledgerbud;
```
*(Make sure the credentials match your `.env` file).*

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
Create all tables and seed default data:
```bash
flask create-db
```

### 4. Run the Application
```bash
python run.py
```
Or via the Flask CLI:
```bash
flask run
```

---

## 🧩 Core Features Implemented
- **Full MVC Structure**: Modular Flask application utilizing Blueprints.
- **Data Foundation**: SQLAlchemy models for Wallet, Transaction, Category, Merchant, Budget, Goal, Subscription, and Audit Logs.
- **ETL Engine**: Drag-and-drop ingestion of PDF/CSV/XLSX statements with parsing via `pdfplumber` and intelligent de-duplication.
- **Financial Intelligence**:
  - Merchant Dictionary Engine (Auto-categorization)
  - Subscription & Recurring Payment Detection
  - Financial Health Scoring (0-100)
  - AI Rule-based Advisory Engine
- **Analytics & What-If**: Visualize spending trends and run simulations to see how minor spending reductions impact 10-year wealth projections.

---
Enjoy gaining deeper insights into your financial health!
