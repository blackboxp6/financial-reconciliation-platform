# FinRecon — Financial Reconciliation and Exception Management Platform

**An end-to-end financial reconciliation platform designed to identify transaction discrepancies, support controlled fuzzy matching, manage financial exceptions, and generate actionable management insights.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-150458)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
![Status](https://img.shields.io/badge/Project-Active%20Development-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 1. Project Overview

FinRecon is a Financial Reconciliation and Exception Management Platform developed to automate the comparison of financial transactions between two independent financial systems, such as a bank and a payment gateway.

In financial operations, transaction records from different systems do not always match. Differences can arise from missing transactions, amount discrepancies, date inconsistencies, duplicate records, delayed processing, and inconsistent transaction identifiers.

Traditional manual reconciliation can be time-consuming, difficult to scale, and prone to human error.

FinRecon addresses these challenges through an automated reconciliation engine, data validation, controlled fuzzy matching, exception classification, human review, audit logging, and management reporting.

The platform is designed not only to identify discrepancies but also to help financial operations teams understand their financial impact, prioritize investigations, and make informed operational decisions.

**Core principle: Reconciliation should not stop at identifying mismatches. It should support investigation, accountability, and resolution.**

## 2. Business Problem

Financial institutions, payment processors, and financial operations teams often need to reconcile transaction records across multiple systems.

For example:

- A payment gateway records a successful transaction, but the corresponding bank transaction is missing.
- A bank records a transaction that does not appear in the gateway.
- The transaction exists in both systems, but the recorded amounts differ.
- Transaction dates differ because of processing delays or settlement timing.
- Duplicate transaction identifiers create uncertainty about the actual number of transactions.
- Different transaction references make it difficult to identify corresponding records.

These discrepancies create operational risks:

- Unresolved financial differences.
- Delayed settlement investigations.
- Increased manual reconciliation effort.
- Incomplete transaction records.
- Duplicate processing risks.
- Limited visibility into outstanding financial exceptions.
- Difficulty tracking investigation decisions and accountability.

FinRecon aims to transform reconciliation from a manual comparison process into a structured and auditable workflow.

## 3. Project Objectives

The primary objectives are to:

1. Automate transaction reconciliation between bank and gateway datasets.
2. Validate and standardize incoming financial records.
3. Identify exact matches and classify discrepancies.
4. Generate potential matches when transaction identifiers differ.
5. Introduce human approval before fuzzy matches are applied.
6. Maintain an audit trail of important reconciliation activities.
7. Quantify financial investigation exposure.
8. Generate management reports that support operational decisions.
9. Establish a foundation for database-backed financial operations and exception management.

## 4. System Architecture

The current architecture separates the reconciliation logic, data validation, reporting, fuzzy matching, and user interface.

```text
                  FINANCIAL DATA SOURCES
                           |
              +------------+------------+
              |                         |
        Bank Transactions       Gateway Transactions
              |                         |
              +------------+------------+
                           |
                    DATA VALIDATION
                           |
              - Required field validation
              - Date normalization
              - Amount validation
              - Duplicate identification
              - Invalid record handling
                           |
                           v
                  RECONCILIATION ENGINE
                           |
              +------------+------------+
              |                         |
          Exact Matching           Exception Detection
              |                         |
              +------------+------------+
                           |
                           v
                   FUZZY MATCHING
                           |
              - Candidate generation
              - Similarity scoring
              - Candidate ranking
              - Mutual-best identification
                           |
                           v
                  HUMAN REVIEW PROCESS
                           |
              +------------+------------+
              |            |            |
           Approved      Rejected      Deferred
              |
              v
              CONTROLLED MATCH APPLICATION
                           |
                           v
                 FINANCIAL REPORTING
                           |
              +------------+------------+
              |            |            |
          KPI Reports   Exception     Audit Logs
                        Priorities
              |
              v
                 STREAMLIT DASHBOARD
                           |
              - Overview
              - Reconciliation
              - Exception Queue
              - Investigation
              - Management Reports
              - Audit History
```

The longer-term architecture introduces PostgreSQL as the operational data store and a dedicated API layer for backend services.

## 5. Implemented Features

### 5.1 Automated Transaction Reconciliation

The reconciliation engine compares transaction records from bank and payment gateway datasets.

Implemented capabilities:

- Transaction ID standardization.
- Date and amount normalization.
- Exact transaction matching.
- Outer-join reconciliation.
- Duplicate transaction identification.
- Discrepancy classification.
- Amount variance calculation.
- Reconciliation summary generation.

Supported reconciliation classifications include:

| Classification | Description |
|---|---|
| MATCHED | Transaction exists in both systems with matching details. |
| AMOUNT_MISMATCH | Transaction exists in both systems, but amounts differ. |
| DATE_MISMATCH | Transaction exists in both systems, but dates differ. |
| AMOUNT_AND_DATE_MISMATCH | Both amount and date differ. |
| MISSING_IN_GATEWAY | Transaction exists in the bank but not in the gateway. |
| MISSING_IN_BANK | Transaction exists in the gateway but not in the bank. |
| Duplicate classifications | Records with duplicate transaction identifiers. |

### 5.2 Data Validation and Quality Controls

The validation module checks incoming records before reconciliation.

Current validation includes:

- Required field verification.
- Missing transaction identifier detection.
- Blank identifier detection.
- Invalid date detection.
- Invalid numeric amount detection.
- Negative amount checks.
- Duplicate identification.

Invalid records are separated from valid records for further inspection.

### 5.3 Fuzzy Matching Engine

Exact matching cannot identify every corresponding transaction.

For example, two systems may record the same underlying payment using different transaction references.

FinRecon implements a fuzzy matching engine that generates potential transaction pairs using multiple similarity features.

Current weighted scoring:

| Feature | Weight |
|---|---:|
| Amount similarity | 35% |
| Date similarity | 30% |
| Transaction type similarity | 15% |
| Channel similarity | 10% |
| Transaction ID similarity | 10% |
| **Total** | **100%** |

The engine also considers:

- Date-window filtering.
- Candidate ranking.
- Mutual-best candidate identification.
- Match confidence scores.
- Review prioritization.
- Candidate-level discrepancy information.

Fuzzy matching is used to generate candidates, not automatically approve transactions.

### 5.4 Human-in-the-Loop Review

Potential fuzzy matches are reviewed before application.

Reviewers can:

- Approve a candidate.
- Reject a candidate.
- Defer a candidate for further investigation.

The review process records:

- Reviewer identification.
- Review decision.
- Review timestamp.
- Review batch identification.
- Candidate similarity score.
- Related transaction identifiers.

Only approved and validated pairs are applied to the reconciliation output.

The application process also checks that a transaction is not matched to multiple counterpart transactions.

### 5.5 Fuzzy Matching Evaluation

A controlled evaluation script tests fuzzy matching against a small dataset containing known genuine and misleading transaction pairs.

Initial evaluation results:

| Metric | Result |
|---|---:|
| True Positives | 3 |
| False Positives | 1 |
| False Negatives | 0 |
| Precision | 75.00% |
| Recall | 100.00% |
| F1 Score | 85.71% |

These results demonstrate the evaluation workflow, not production-level model performance. A larger labeled dataset and more extensive testing are required before deploying fuzzy matching in a live financial environment.

### 5.6 Financial Reporting

FinRecon generates financial reconciliation reports containing:

- Total reconciliation records.
- Exact matches.
- Approved fuzzy matches.
- Outstanding exceptions.
- Amount discrepancies.
- Missing bank transactions.
- Missing gateway transactions.
- Duplicate records.
- Financial investigation exposure.

The reporting layer also generates machine-readable JSON reports and exception-priority CSV files.

### 5.7 Audit Logging

The project includes an audit logging module that records important workflow events.

Current event information includes:

- Event ID.
- Run ID.
- Timestamp.
- Event type.
- Status.
- Event details.

The current implementation uses CSV-based logging. A database-backed and access-controlled audit architecture is planned.

### 5.8 Management Reporting and Exception Prioritization

FinRecon includes a management reporting script that converts reconciliation results into operational insights.

It provides:

- Reconciliation performance indicators.
- Outstanding exception counts.
- Financial investigation exposure.
- Fuzzy review statistics.
- Management recommendations.
- Exception prioritization outputs.

The objective is to help decision-makers identify which discrepancies require attention first.

## 6. Demonstration Results

The following results were generated from a synthetic dataset containing 10,000 bank transaction records and approximately 10,100 gateway transaction records.

### Reconciliation Performance

| Metric | Result |
|---|---:|
| Total output records | 10,188 |
| Exact matches | 9,204 |
| Approved fuzzy matches | 12 |
| Total matched pairs | 9,216 |
| Output-row match rate | 90.46% |

### Outstanding Exceptions

| Exception Type | Count |
|---|---:|
| Missing in gateway | 188 |
| Missing in bank | 187 |
| Amount mismatches | 298 |
| Date mismatches | 199 |
| Combined mismatches | 0 |
| Duplicates | 100 |

### Financial Investigation Exposure

| Category | Amount |
|---|---:|
| Amount mismatch exposure | PHP 1,432,981.85 |
| Missing gateway value | PHP 9,011,327.19 |
| Missing bank value | PHP 9,046,096.50 |
| Gross investigation amount | PHP 19,490,405.54 |

### Fuzzy Review Performance

| Metric | Result |
|---|---:|
| Candidates generated | 19 |
| Candidates reviewed | 19 |
| Approved | 12 |
| Rejected | 7 |
| Deferred | 0 |
| Acceptance rate | 63.16% |

**Important interpretation:** These are results from a synthetic demonstration dataset. The 90.46% figure is an output-row match rate, not a universal transaction-level reconciliation KPI. Financial investigation exposure represents amounts requiring investigation, not confirmed financial losses. The gross exposure measure may include economically overlapping amounts.

## 7. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and business logic |
| Pandas | Data processing and reconciliation |
| Streamlit | Interactive dashboard |
| Plotly | Data visualization |
| SQLAlchemy | Database ORM foundation |
| PostgreSQL | Planned operational database |
| Psycopg | PostgreSQL connectivity |
| Python-dotenv | Environment configuration |
| JSON | Structured reporting |
| CSV | Data ingestion and report export |
| Pytest | Automated testing |

## 8. Project Structure

```text
financial-reconciliation-platform/
│
├── app.py
│
├── backend/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   └── init_db.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── reconciliation/
│   ├── __init__.py
│   ├── engine.py
│   ├── reporting.py
│   ├── audit.py
│   ├── validation.py
│   └── fuzzy_matching.py
│
├── scripts/
│   ├── generate_sample_data.py
│   ├── evaluate_fuzzy_matching.py
│   ├── review_fuzzy_candidates.py
│   ├── apply_approved_fuzzy_matches.py
│   ├── validate_fuzzy_application.py
│   └── generate_management_report.py
│
├── tests/
│   └── test_engine.py
│
├── run_reconciliation.py
├── test_validation_manual.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Some components, particularly the database foundation, are under active development. The structure may evolve as the platform becomes database-backed.

## 9. Installation and Setup

### Prerequisites

- Python 3.10 or later.
- Git.
- Visual Studio Code or another Python IDE.
- Windows, Linux, or macOS.

PostgreSQL is required for the database-backed development phase, but the existing CSV-based reconciliation workflow can be run independently.

### Step 1: Clone the Repository

```bash
git clone https://github.com/blackboxp6/financial-reconciliation-platform.git

cd financial-reconciliation-platform
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 4: Generate Synthetic Data

```bash
python scripts/generate_sample_data.py
```

This generates sample bank and gateway transaction datasets in the `data/raw/` directory.

### Step 5: Run Reconciliation

```bash
python run_reconciliation.py
```

The reconciliation process generates output files in `data/processed/`.

### Step 6: Generate Management Reports

```bash
python scripts/generate_management_report.py
```

### Step 7: Launch the Dashboard

```bash
streamlit run app.py
```

The application should open in your browser.

### Optional: Initialize the PostgreSQL Database

For the database-backed development phase:

1. Install and start PostgreSQL.
2. Create the `finrecon` database and application user.
3. Configure the `DATABASE_URL` in your local `.env` file.
4. Install the database dependencies.
5. Initialize the schema:

```bash
python -m backend.init_db
```

Never commit your actual `.env` file or database credentials.

## 10. Configuration

The application uses environment variables for local configuration.

Example `.env.example`:

```env
DATABASE_URL=postgresql+psycopg://finrecon_app:YOUR_PASSWORD@localhost:5432/finrecon
```

Copy this file to `.env` and replace the placeholder values with your local configuration.

The `.env` file must remain excluded from Git.

## 11. Testing and Validation

The project includes scripts for evaluating reconciliation and fuzzy matching behavior.

Run the existing test suite:

```bash
python -m pytest -v
```

Run fuzzy matching evaluation:

```bash
python scripts/evaluate_fuzzy_matching.py
```

Validate fuzzy match application:

```bash
python scripts/validate_fuzzy_application.py
```

These checks help verify matching behavior, application integrity, and consistency between original and updated reconciliation results.

## 12. Future Development Roadmap

FinRecon is being developed toward a more complete, production-oriented financial operations platform.

| Phase | Planned Development |
|---|---|
| 1 | PostgreSQL database foundation |
| 2 | Transaction ingestion and source batch management |
| 3 | Database-backed reconciliation runs |
| 4 | Exception case management |
| 5 | Investigation workspace and SLA tracking |
| 6 | Supervisor approval and separation of duties |
| 7 | Improved fuzzy matching and evaluation |
| 8 | Database-backed audit and compliance controls |
| 9 | Operational analytics and management dashboards |
| 10 | FastAPI backend and authentication |
| 11 | Automated testing, monitoring, and reliability |
| 12 | Docker deployment and production infrastructure |

### Planned Enterprise Capabilities

The longer-term objective is to introduce:

- Role-based access control.
- Analyst and supervisor permissions.
- Exception ownership and assignment.
- Investigation lifecycle management.
- Resolution codes and supporting evidence.
- Approval workflows.
- Exception aging and SLA monitoring.
- Idempotent transaction ingestion.
- Database migrations.
- Structured application logging.
- Monitoring and alerting.
- Backup and recovery procedures.
- Secure deployment architecture.

## 13. Design Principles

FinRecon is being developed around several important engineering and financial control principles.

**1. Data Integrity**

Original financial records should be preserved. Reconciliation outcomes should be stored separately from source transactions.

**2. Controlled Automation**

Fuzzy matching should generate possible relationships, not silently change financial records. Human review and appropriate approval controls are required.

**3. Auditability**

Important actions should be traceable to an actor, timestamp, affected record, and relevant change.

**4. Separation of Duties**

Sensitive investigation and resolution activities should support independent approval rather than allowing one person to control the entire process.

**5. Financial Accountability**

Discrepancies should be quantified and prioritized without incorrectly treating investigation exposure as confirmed financial loss.

**6. Scalability**

The system should progressively move from file-based processing toward database-backed services and scalable infrastructure.

## 14. Current Limitations

This project is actively being developed and is not yet a production-ready banking system.

Current limitations include:

- Synthetic demonstration data rather than live banking integrations.
- CSV-based audit logging rather than protected database-backed audit storage.
- Fuzzy matching evaluated on a small controlled sample.
- Candidate generation that requires further optimization for large transaction volumes.
- Initial database foundation that still needs integration with the reconciliation workflow.
- Further authentication, authorization, approval, monitoring, and recovery controls required.

No live banking credentials, customer information, or confidential financial records should be used in the demonstration environment.

## 15. Potential Applications

The architecture and concepts demonstrated by FinRecon are relevant to:

- Banking operations.
- Payment gateway reconciliation.
- Digital payment processing.
- Financial technology companies.
- Accounting and finance operations.
- Settlement monitoring.
- Internal audit and financial control.
- Transaction exception management.

## 16. Project Vision

The long-term vision is to develop FinRecon into a unified financial reconciliation and exception management platform.

Rather than simply comparing two files, the system aims to support the complete operational lifecycle:

**Ingest → Validate → Reconcile → Detect → Prioritize → Investigate → Approve → Resolve → Report**

The goal is to combine software engineering, data processing, financial controls, and decision-support analytics into one platform.

---

## 17. Author and Project Information

**Project:** FinRecon — Financial Reconciliation and Exception Management Platform

**Development focus:**
- Financial data engineering.
- Automated reconciliation.
- Fuzzy matching.
- Exception management.
- Financial analytics.
- Database engineering.
- Operational decision support.

**Repository:** [GitHub Repository](https://github.com/blackboxp6/financial-reconciliation-platform)

---

*FinRecon is an independent development and portfolio project using synthetic data. It is not affiliated with or endorsed by any bank, payment gateway, or financial institution.*