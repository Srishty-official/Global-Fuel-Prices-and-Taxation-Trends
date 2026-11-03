# Global Fuel Prices and Taxation Trends Analytics Platform

An enterprise-ready, end-to-end fullstack data analytics and visualization platform built with **Python, Flask, SQLite 3, Pandas, and Chart.js**, featuring complete RESTful CRUD endpoints, custom SQL calculated views, streaming exports, and **Tableau Public** business intelligence integration.

![Platform Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue)
![Database](https://img.shields.io/badge/Database-SQLite%203-lightgrey)
![Frontend](https://img.shields.io/badge/Frontend-Chart.js%20%7C%20CSS3-orange)

---

## 1. Executive Summary & Features

This platform decomposes retail fuel prices across 10 major global economies over a six-year observation horizon (2019–2024). It isolates sovereign tax policies from underlying industrial crude and refining costs.

### Key Architectural Capabilities
- **ACID-Compliant Relational Database (`fuel_prices.db`):**
  - Domain constraints (`CHECK` on positive price, tax between 0% and 100%, valid years).
  - Composite uniqueness: `UNIQUE(country, year, fuel_type)` prevents duplicate records.
  - Multi-column indexes on `(country, year, fuel_type)` for sub-millisecond query execution.
  - Analytical SQL views: `v_fuel_analytics`, `v_country_summary`, `v_year_trends`.
- **Fullstack RESTful API:**
  - `GET /api/data`: Dynamic filtering by country, year, fuel type, search keyword, price/tax bounds, multi-column sorting, and limit/offset pagination.
  - `GET /api/summary`: Computes aggregate means, minimums, maximums, fuel spreads, and real-time **Pearson correlation coefficient ($r$)**.
  - `POST /api/records`: Create new observations with strict server-side validation.
  - `GET /api/records/<id>`: Retrieve single observation.
  - `PUT /api/records/<id>`: Update observation with validation.
  - `DELETE /api/records/<id>`: Remove observation with transactional rollback safety.
  - `POST /api/reset-db`: Reset database to baseline seed state from CSV.
  - `GET /api/export/csv`: Stream filtered observations as a formatted CSV file.
  - `GET /api/export/json`: Stream observations as structured JSON.
  - `GET /api/audit`: Database integrity check, anomaly detection, and query benchmark latency.
- **Executive Frontend Dashboard (`templates/index.html`):**
  - Real-time AJAX reactive filtering without full-page reloads.
  - Six executive KPI metric tiles with min/max indicators and Pearson correlation interpretation.
  - **Five Interactive Visualizations (Chart.js):**
    1. *Price Trajectory:* Multi-series line chart (Overall, Petrol, Diesel).
    2. *Tax Share Comparison:* Ranked bar chart with color-coded severity brackets.
    3. *Scatter Plot & Correlation:* Scatter matrix with linear regression trend.
    4. *Cost Decomposition:* Stacked bar chart isolating Pre-tax base cost from Government tax levy.
    5. *Fuel Type Disparity:* Grouped comparison of Petrol vs. Diesel spreads.
  - **Interactive 3-Scene Narrative Story Mode:** Clickable scene cards that automatically adjust dashboard focus, filters, and chart animations.
  - **In-Table Data Management:** Search, multi-column sort, client pagination (15 per page), inline editing modals, and row deletion.
- **Tableau Analytics Integration (`templates/tableau.html`):**
  - Published Tableau Public iframe embed frame with preset energy dashboard demos.
  - Fallback **Interactive Visual Simulator** rendering Tableau's exact 3-sheet layout directly from SQLite data.
  - Step-by-step connection guide for Tableau Desktop and Tableau Public.

---

## 2. Quick Start & Setup

### Option A: One-Click Runner (Windows)
Double-click `run.bat` or run in PowerShell:
```powershell
.\run.ps1
```

### Option B: Standard Python Setup
```bash
# 1. Navigate to directory
cd Fuel_Prices_Project

# 2. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch application
python app.py
```
Open your browser to: **`http://127.0.0.1:5000`**

*Note:* On initial startup, `app.py` automatically initializes `fuel_prices.db`, applies `schema.sql`, and seeds the 120 baseline observations from `data/fuel_prices.csv`.

---

## 3. Automated Test Suite

Run the comprehensive unit test suite covering database constraints, REST API endpoints, CRUD operations, calculations, and exports:
```bash
python -m unittest tests/test_app.py
```
All 10 test cases run in $< 1.5$ seconds and verify:
- Relational schema and view creation
- UI routes (`/` and `/tableau`)
- Filtered API data retrieval and calculated field accuracy
- Pearson correlation statistical calculations
- Complete CRUD lifecycle (Create $\to$ Read $\to$ Update $\to$ Delete)
- Rejection of invalid inputs (negative prices, out-of-range tax)
- CSV and JSON export streams
- System diagnostics and audit integrity checks

---

## 4. Calculated Fields Formulation

All observations decompose the retail fuel price into its fiscal and pre-fiscal economic elements:

| Calculated Field | Formula | Economic Significance |
|---|---|---|
| **Estimated Tax Component** | $P_{\text{retail}} \times \left(\frac{\text{Tax}\%}{100}\right)$ | Sovereign monetary quantum collected per litre sold. |
| **Estimated Pre-tax Component** | $P_{\text{retail}} \times \left(1 - \frac{\text{Tax}\%}{100}\right)$ | Base industrial cost (crude extraction, refining margin, shipping, wholesale margin). |
| **Tax-to-Pretax Ratio** | $\frac{\text{Tax}\%}{100 - \text{Tax}\%}$ | Ratio of fiscal tax levy relative to underlying industrial cost. |
| **Pearson Correlation ($r$)** | $\frac{\sum (X - \bar{X})(Y - \bar{Y})}{\sqrt{\sum(X-\bar{X})^2 \sum(Y-\bar{Y})^2}}$ | Quantifies linear association between tax rate and consumer price. |

---

## 5. API Reference Guide

### 1. Data Retrieval
```http
GET /api/data?country=India&year=2023&fuel_type=Petrol
```
**Response:**
```json
[
  {
    "id": 10,
    "country": "India",
    "year": 2023,
    "fuel_type": "Petrol",
    "price_usd_per_litre": 1.156,
    "tax_percent": 29.17,
    "currency": "USD",
    "estimated_tax_component": 0.337,
    "estimated_pre_tax_component": 0.819,
    "tax_to_pretax_ratio": 0.412,
    "source_note": "Official OECD/IEA & World Bank Series"
  }
]
```

### 2. Statistical Summary
```http
GET /api/summary?year=2024
```
**Response:**
```json
{
  "records": 20,
  "countries": 10,
  "avg_price": 1.482,
  "min_price": 0.965,
  "max_price": 1.876,
  "avg_tax": 37.42,
  "min_tax": 16.92,
  "max_tax": 53.44,
  "correlation": 0.816,
  "avg_tax_component": 0.584,
  "avg_pre_tax_component": 0.898,
  "petrol_avg": 1.512,
  "diesel_avg": 1.452
}
```

### 3. Create Record
```http
POST /api/records
Content-Type: application/json

{
  "country": "Brazil",
  "year": 2025,
  "fuel_type": "Petrol",
  "price_usd_per_litre": 1.250,
  "tax_percent": 28.50,
  "source_note": "ANP Brazil Monthly Energy Report"
}
```

### 4. Update & Delete
- `PUT /api/records/<id>`: Update record fields.
- `DELETE /api/records/<id>`: Remove record by ID.

### 5. Diagnostics Audit
```http
GET /api/audit
```
**Response:**
```json
{
  "status": "healthy",
  "integrity_check": "ok",
  "total_records": 120,
  "duplicates_detected": 0,
  "outliers_detected": 0,
  "unique_countries": 10,
  "unique_years": 6,
  "query_latency_ms": 2.14,
  "pandas_available": true
}
```

---

## 6. Project Flow & Verification Checklist

| Project Milestone | Implementation Artifact | Status |
|---|---|---|
| **Problem & Economics** | Executive summary, econometric methodology, and problem statement | Completed |
| **Data Collection** | Standardized 10-country, 6-year dataset (120 observations) in `data/fuel_prices.csv` | Completed |
| **Relational Storage** | SQLite `fuel_prices.db` with ACID constraints, composite indexes, and views in `schema.sql` | Completed |
| **Data Preparation** | Pandas and stdlib ETL normalization, type conversion, and sanitization | Completed |
| **Calculated Fields** | Tax component, pre-tax cost, and fiscal ratio in SQL views and Python API | Completed |
| **Visualizations** | 5 Chart.js charts: Trend line, Ranked bar, Scatter correlation, Stacked decomposition, Grouped fuel spread | Completed |
| **Dashboard UI** | Glassmorphism dashboard with AJAX filters, KPI cards, table pagination, and modals | Completed |
| **Story Mode** | 3-scene interactive narrative (Global Shock, Tax Divergence, Cost Convergence) | Completed |
| **Tableau BI** | `/tableau` route with live embed support, preset BI links, and fallback interactive simulator | Completed |
| **Performance Audit** | `/api/audit` endpoint, sub-5ms SQL latency, automated duplicate checks | Completed |
| **Automated Testing** | 10 unit and integration tests in `tests/test_app.py` | Completed |
| **Documentation & Script** | Comprehensive `PROJECT_REPORT.md` including 5-minute video demonstration script | Completed |

---

## 7. License & Academic Attribution
Developed for educational data analytics, fullstack web development, and business intelligence coursework. Observation data is harmonized from OECD Energy Statistics, IEA Fuel Price Reports, and World Bank Indicators.

AUTHOR
**SRISHTY CHATTERJEE**
