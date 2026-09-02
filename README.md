# E-COMMERCE DATA ENGINEERING & AGENTIC AI PLATFORM

> An end-to-end enterprise platform combining **3-Tier Medallion Data Engineering Pipelines**, **Data Science & ML Forecasting**, **Business Intelligence Dashboards**, and an **Autonomous 9-Agent AI Engine** powered by Google Gemini and PostgreSQL.

---

## 🌟 Executive Summary

This platform bridges the gap between complex enterprise data pipelines and executive decision-making. 

In large E-Commerce organizations, millions of daily customer orders generate raw data across multiple formats. Business leaders often wait days for data engineering teams to write custom database queries or build manual reports.

**My Solution:**
1. **Automated Data Engineering Pipeline:** Ingests raw data, cleans and standardizes it through a **Medallion Architecture (Bronze → Silver → Gold)**, handles historical location tracking using **SCD Type 1 & Type 2**, and structures analytics into a high-performance **Dimensional Star Schema**.
2. **Data Science & ML Engine:** Computes trend regression slopes, moving averages, Z-score revenue anomaly detection, and linear extrapolation sales forecasting.
3. **Autonomous Agentic AI Engine:** A team of 9 specialized AI agents connected directly to the Gold PostgreSQL database that converts plain English questions into safe, read-only SQL queries, Plotly visual graphs, evidence-grounded business insights, and practical management recommendations.

---

## 🏗️ End-to-End System Architecture

```
[ RAW SOURCE FEEDS ]
  Orders • Customers • Sellers • Products • Payments
          │
          ▼
🟫 BRONZE LAYER (Raw PostgreSQL Schema)
  Append-only storage with batch IDs & metadata audit logs
          │
          ▼
🥈 SILVER LAYER (Cleansed & Standardized Schema)
  Date/Currency parsing, deduplication, state lookups & SCD Type 2 history
          │
          ▼
🥇 GOLD LAYER (Dimensional Star Schema)
  Fact Sales • Customer Dim • Product Dim • Seller Dim • Date Dim • Revenue Mart
          │
          ├───────────────────────────────┐
          ▼                               ▼
🧠 ML & STATISTICAL ENGINE         🤖 MULTI-AGENT AI SYSTEM (Gemini API)
  Regression • Z-Score • Forecast     Auto Router • Data Agent • Insight Agent • Action Agent
          │                               │
          └───────────────────────────────┤
                                          ▼
                         📊 STREAMLIT BI PRESENTATION UI
                           Interactive AI Analyst Chatbot
```

---

## 🛠️ Technology Stack

| Domain | Technology / Tool | Usage & Scope |
|---|---|---|
| **Database** | PostgreSQL 14 | Multi-schema architecture (`bronze`, `silver`, `gold`, `metadata`) |
| **Orchestration** | Apache Airflow 2.8 (Docker) | Automated DAG scheduling (`01_bronze_ingestion`, `02_silver_transform`, `03_gold_aggregation`) |
| **Language & Libraries** | Python 3.12, Pandas, NumPy, SQLAlchemy | Data manipulation, transformation, and SQLAlchemy ORM connection pool |
| **AI & LLM Engine** | Google Gemini API (`gemini-3.6-flash`) | Multi-agent semantic routing, safe SQL generation, insight discovery, and action recommendations |
| **Machine Learning** | SciPy / NumPy Polyfit / Scikit-Learn | Linear trend regression, Z-score anomaly detection, moving averages, sales forecasting |
| **Data Quality** | Great Expectations | Non-null validations, range constraints, referential integrity checks |
| **Presentation UI** | Streamlit 1.36 + Plotly Express | Dark-theme BI dashboard, interactive AI chat prompt, prompt chips, live status badges |
| **Containerization** | Docker & Docker Compose | Containerized local execution for PostgreSQL and Apache Airflow |

---

## ⚙️ 1. Data Engineering Architecture

### A. Medallion Storage Model
- **Bronze Layer (`bronze.*`):** Preserves raw ingested files without modification. Tracks batch run IDs, source filenames, and ingestion timestamps.
- **Silver Layer (`silver.*`):** Standardizes date formats into ISO standard, casts currency strings to `NUMERIC(12,2)`, strips whitespace, joins product categories with English lookups, and applies **SCD Type 2** rules for customer/seller relocations.
- **Gold Layer (`gold.*`):** A fully optimized **Star Schema** dimensional model:
  - `gold.fact_sales`: Central fact table storing sales measures (`price`, `freight_value`, `total_item_value`, `payment_value`, `delivery_days`) with surrogate key references.
  - `gold.dim_customer`: Customer dimension with state, region, and SCD2 versioning columns.
  - `gold.dim_product`: Product dimension with English category names and physical size classifications (`Small`, `Medium`, `Large`).
  - `gold.dim_seller`: Seller dimension with geographic regions.
  - `gold.dim_date`: Date dimension (2017–2025) with year, quarter, month, week of year, and weekend flags.
  - `gold.revenue_mart`: Pre-aggregated data mart with SQL window functions computing `mom_growth_pct`, `cumulative_revenue`, and monthly revenue ranks.

### B. Slowly Changing Dimensions (SCD Type 1 & 2)
- **SCD Type 1 (Overwrite):** Applied to `gold.dim_product` for non-historical attributes (weight, size category, description length). Uses PostgreSQL `ON CONFLICT (product_id) DO UPDATE SET...`.
- **SCD Type 2 (Historical Versioning):** Applied to `gold.dim_customer` and `gold.dim_seller`. When a customer or seller moves to a new city/state:
  1. The current active record is expired (`effective_end_date = CURRENT_DATE`, `is_current = FALSE`).
  2. A new version record is inserted (`version_number = version_number + 1`, `is_current = TRUE`).
  3. *Business Impact:* Historical sales remain credited to the original region, while new sales go to the new state.

### C. Data Quality & Metadata Auditing
- **Expectation Checks:** Validates primary key presence, non-null mandatory fields, positive prices (`price > 0`), and referential integrity between fact foreign keys and dimension surrogate keys.
- **Metadata Audit Trail (`metadata.*`):** Records pipeline execution metrics in `metadata.pipeline_runs`, data quality check results in `metadata.dq_results`, and source load timestamps in `metadata.watermarks`.

---

## 🔬 2. Data Science & Machine Learning Engine

The system incorporates an embedded Machine Learning and Statistical Engine operating on the Gold analytical data layer:

1. **Linear Trend Regression:** Computes regression slopes on monthly revenue time-series (`gold.revenue_mart`) to identify whether sales trajectories are increasing or decreasing.
2. **Z-Score Anomaly Detection:** Calculates statistical Z-scores across monthly revenue. Periods where `|Z| > 2.0` are automatically flagged as unusual business revenue anomalies.
3. **Revenue Forecasting:** Extrapolates monthly revenue for 1 to 12 months ahead using linear regression trend extrapolation (`numpy.polyfit`).
4. **Moving Average Trend Line:** Computes 3-period moving averages (`MA-3`) to smooth out short-term fluctuations and highlight underlying growth.

---

## 🤖 3. Agentic AI Multi-Agent Architecture

Rather than relying on a single monolithic LLM prompt, the platform implements an autonomous **Multi-Agent System** where 9 specialized AI agents work together:

| Agent Name | Icon | Core Responsibility | Output / Mechanism |
|---|---|---|---|
| **Auto Router** | 🤖 | Intent classification & pipeline planning | Returns ordered execution chain e.g. `["data", "insight", "action"]` |
| **Data Agent** | 📊 | Database & SQL Expert | Generates safe PostgreSQL SELECT queries on Gold Star Schema tables |
| **ML Agent** | 🧠 | Statistician & Anomaly Analyst | Computes regression slopes, moving averages, and Z-score anomalies |
| **Forecast Agent** | 🔮 | Predictor & Trend Extrapolator | Predicts future revenue for 1–12 months with Plotly visual forecast lines |
| **Insight Agent** | 💡 | Business Analyst | Transforms raw query data into 2–4 sentence evidence-grounded insights |
| **Action Agent** | 🎯 | Management Consultant | Recommends specific operational actions with business rationale |
| **Report Agent** | 📋 | Executive Assistant | Summarizes overall dashboard data into an executive summary |
| **Pipeline Agent** | ⚙️ | Data Engineering Auditor | Queries `metadata.pipeline_runs` & `metadata.dq_results` for pipeline health |
| **General Agent** | 💬 | Technical Advisor | Answers tech-stack queries on Airflow, PostgreSQL, Docker, and Medallion architecture |

### Example Multi-Agent Workflow:
User asks: *"Why did profit decrease and what should management do?"*
1. **Auto Router 🤖** → Selects `Data Agent 📊 → Insight Agent 💡 → Action Agent 🎯`.
2. **Data Agent 📊** → Generates SQL, queries Gold DB, and retrieves sales metrics ($1.8M total revenue).
3. **Insight Agent 💡** → Analyzes data: *"Category X sales declined by 12% MoM due to an 18% spike in regional freight costs."*
4. **Action Agent 🎯** → Recommends: *"Action: Renegotiate regional freight agreements and offer discount bundles on Category X."*
5. **Presentation** → Streamlit renders generated SQL code, data table, Plotly bar chart, Insight Card, and Action Card.

---

## 📊 4. Business Intelligence & UI Features

- **Interactive AI Analyst Chatbot Landing Page:** Interactive prompt input, 8 instant suggested prompt chips (*"Total sales?"*, *"Top 10 products?"*, *"Sales forecast?"*), and clear chat button.
- **Live Connection Status Badges:** Top-right green lights displaying live connection health for `Gemini: Connected (🟢)`, `Database: Connected (🟢)`, and `Pipeline: Connected (🟢)`.
- **4 Executive Dashboard Pages:**
  1. **Overview:** 6 KPI cards (Total Revenue, Orders, Customers, Products, AOV, Growth MoM), category bar charts, revenue trend lines.
  2. **Pipeline Monitor:** Visual Medallion architecture flow and run execution logs.
  3. **Data Quality:** Validation report details, average DQ scores, and failure count graphs.
  4. **ML Insights:** Moving average lines, Z-score anomaly threshold graphs, and MoM growth rate breakdown.

---

## 🔒 5. Security & Rate-Limit Safety

- **Read-Only Query Validator:** The Data Agent enforces a strict SQL security check blocking destructive commands (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`). Only single-statement `SELECT` and `WITH` queries are allowed.
- **Secret Protection:** API keys and database credentials are managed strictly via environment variables (`.env`) and excluded from source control (`.gitignore`).
- **Quota Protection:** Fast deterministic pattern fallbacks prevent Gemini API rate limits (HTTP 429) during rapid query testing.

---

## 🚀 Quickstart & How to Run

### Prerequisites
- Docker Desktop
- Python 3.12+

### 1. Run Pipeline & Start App
```bash
# 1. Start PostgreSQL & Airflow (Docker)
docker-compose up -d

# 2. Run Data Pipeline Ingestion
python scripts/run_full_pipeline.py

# 3. Launch Streamlit AI Platform & Chatbot
streamlit run agent_dashboard.py
```

### 2. Access Web Interfaces
- **AI Analyst & BI Dashboard:** [http://localhost:8501](http://localhost:8501)
- **Apache Airflow UI:** [http://localhost:8080](http://localhost:8080) *(User: `admin` | Password: `admin123`)*

---

## 📄 Project Documentation

- 📄 **[PDF Project Report](Data_Engineering_Agentic_AI_Final_Report.pdf):** Complete, plain-English report detailing every technical requirement.
- 📊 **[PowerPoint Presentation](ECommerce_Agentic_AI_Presentation.pptx):** Widescreen 8-slide presentation deck.

---

## 📝 License
This project is open-source and available under the **MIT License**.
