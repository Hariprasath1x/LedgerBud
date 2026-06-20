# LedgerBud – Smart Statement Ingestion & Financial Intelligence Phase

## Project Context

LedgerBud is being developed as a Financial Intelligence Platform rather than a simple expense tracker.

The long-term vision is to help users:

* Track spending
* Manage budgets
* Monitor financial goals
* Improve financial health
* Detect recurring expenses
* Analyze spending behavior
* Receive AI-driven financial guidance

The platform already includes or plans to include:

* User Authentication
* Multi-Wallet Management
* Transaction Management
* Budget Management
* Dashboard & Analytics
* Merchant Dictionary Engine
* Auto Categorization
* Financial Health Score
* Spending Insights Engine
* Recurring Expense Detection
* Subscription Tracker
* Goal-Based Savings
* Net Worth Tracking
* AI Financial Advisor
* What-If Analysis
* Audit Logging
* Analytics Warehouse

This phase focuses on redesigning how financial data enters the system.

---

# Problem With Current Import Approach

The current design supports importing:

* CSV files
* Excel files

While technically functional, this is not representative of how real users interact with financial institutions.

Most users receive financial records through:

* Bank statement PDFs
* Credit card statement PDFs
* e-Passbooks
* Downloaded account statements

Very few users regularly export CSV or Excel files.

As a result, a CSV-only workflow creates friction and does not resemble modern fintech products.

---

# Strategic Product Shift

Replace the existing CSV/XLSX Import Module with a comprehensive:

## Smart Statement Ingestion Engine

This should become the primary entry point for financial data.

The platform must support:

### Primary Sources

* Bank Statement PDFs
* Credit Card Statement PDFs
* e-Passbooks

### Secondary Sources

* CSV
* XLSX

PDF should be treated as the first-class import format.

---

# Product Vision

A user should be able to upload a bank statement and immediately receive:

* Extracted transactions
* Merchant identification
* Category mapping
* Spending analysis
* Subscription detection
* Dashboard updates
* Financial insights

without manually entering data.

The import process should feel similar to a modern fintech application.

---

# Core User Flow

Upload Statement

↓

Detect Statement Type

↓

Extract Transaction Data

↓

Validate Records

↓

Normalize Data

↓

Detect Merchants

↓

Map Categories

↓

Load Transactions

↓

Generate Analytics

↓

Update Financial Intelligence Features

---

# Design Philosophy

The ingestion engine should not be designed around specific banks.

Instead, it should focus on identifying transaction information from structured financial statements regardless of institution.

The solution should be:

* Flexible
* Extensible
* Bank agnostic
* Maintainable

The architecture should support future expansion without redesign.

---

# Statement Types To Support

The system should be designed to handle statements from common Indian banks including:

* SBI
* HDFC
* ICICI
* Axis Bank
* Canara Bank
* Indian Bank
* Union Bank
* Bank of Baroda

Support for additional institutions should be easy to add.

---

# Expected Extraction Capabilities

The system should identify and extract financial transaction information such as:

* Transaction Date
* Description
* Merchant
* Debit Amount
* Credit Amount
* Balance
* Reference Number
* Transaction Type

Different banks use different terminology.

The platform should normalize these differences into a consistent internal model.

---

# Statement Intelligence Layer

Financial statements contain more than raw transaction data.

The platform should identify:

* Statement period
* Institution
* Account details
* Transaction count
* Date range

This metadata should improve user trust and create a professional import experience.

---

# Merchant Intelligence

One of the most important platform capabilities is merchant understanding.

Transaction descriptions are noisy and inconsistent.

Examples:

SWIGGY INDIA

SWIGGY ONLINE

UPI/SWIGGY

AMAZON PAY

AMAZON INDIA

NETFLIX INDIA

The system should derive a clean merchant identity from transaction descriptions.

The merchant layer should become a reusable capability throughout LedgerBud.

---

# Merchant Categorization Integration

The ingestion process should integrate directly with the existing Merchant Dictionary Engine.

Examples:

Swiggy → Food

Uber → Travel

Amazon → Shopping

Netflix → Entertainment

Spotify → Entertainment

Unknown merchants should remain uncategorized until reviewed by the user.

Users should always retain control over category assignment.

---

# ETL Philosophy

The ingestion system should demonstrate real-world Data Engineering concepts.

The workflow should clearly separate:

## Extract

Acquire raw data from uploaded statements.

## Transform

Perform:

* Validation
* Standardization
* Cleaning
* Deduplication
* Merchant normalization
* Category mapping

## Load

Persist validated transactions into LedgerBud.

The ETL layer should be reusable and independent from the user interface.

---

# Data Quality Requirements

The transformation layer should handle:

### Duplicate Detection

Transactions with matching:

* Date
* Amount
* Merchant

should be evaluated for duplication.

### Missing Values

Incomplete records should be handled gracefully.

### Date Standardization

All date formats should be normalized.

### Merchant Standardization

Merchant names should be normalized into canonical values.

### Category Assignment

Known merchants should automatically receive categories.

---

# Preview Before Import

Users should never import data blindly.

Before committing transactions, LedgerBud should provide:

* Detected institution
* Statement period
* Transaction count
* Sample transaction preview
* Predicted categories

This step improves transparency and user confidence.

---

# Import Transparency

After processing, the platform should generate an import summary.

Examples:

* Total records processed
* Successfully imported records
* Duplicate records
* Failed records
* Processing statistics

The user should understand exactly what happened during import.

---

# Import History

LedgerBud should maintain historical import records.

Users should be able to review:

* Previous imports
* Import dates
* Statement sources
* Processing outcomes
* Error summaries

This creates accountability and traceability.

---

# Analytics Integration

Imported transactions should automatically participate in:

* Dashboard Metrics
* Spending Insights
* Budget Analysis
* Financial Health Score
* Goal Tracking
* Subscription Detection
* Net Worth Calculations
* What-If Analysis

The ingestion layer is the foundation of all downstream intelligence.

---

# Data Warehouse Integration

LedgerBud contains both operational and analytical workloads.

The ingestion process should support future loading into the Analytics Warehouse.

Warehouse concepts include:

* Fact Transactions
* User Dimension
* Wallet Dimension
* Category Dimension
* Date Dimension

Operational transaction storage and analytical reporting should remain logically separated.

---

# AI Advisor Integration

The AI Financial Advisor should never depend on raw uploaded statements.

Instead:

Imported Transactions

↓

Analytics Layer

↓

Financial Summary

↓

AI Advisor

The AI layer should consume summarized financial context rather than raw transaction records.

This improves privacy, performance, and maintainability.

---

# Auditability

Every import operation should generate audit records.

Examples:

* Statement Uploaded
* Transactions Imported
* Duplicates Removed
* Category Mappings Applied

Auditability is a core platform requirement.

---

# User Experience Principles

The import experience should be:

* Fast
* Predictable
* Transparent
* Explainable
* Professional

Users should understand:

* What was detected
* What was imported
* What was rejected
* Why specific decisions were made

---

# Non-Functional Goals

The system should be designed for:

## Scalability

Support statements containing large numbers of transactions.

## Reliability

Failed imports should never corrupt financial data.

## Extensibility

Future statement formats should be easy to support.

## Maintainability

Extraction logic should remain modular and testable.

## Performance

Large imports should remain responsive.

---

# Future Roadmap Considerations

The architecture should remain compatible with future enhancements including:

* OCR Support
* Scanned Statements
* Mobile Banking Screenshots
* Email Statement Parsing
* Open Banking Integrations
* Automated Account Syncing

These capabilities should be possible without redesigning the ingestion pipeline.

---

# Technical Direction

Claude should evaluate and propose the best architecture, services, workflows, database structures, APIs, background processing strategy, validation mechanisms, ETL implementation, UI flow, and integration approach.

Avoid implementing this as a simple file uploader.

Treat it as a production-style fintech statement ingestion platform that becomes the primary data acquisition layer for LedgerBud.

The final solution should strengthen LedgerBud as a Financial Intelligence Platform and significantly improve its Data Engineering, Backend Engineering, Analytics, and FinTech portfolio value.
