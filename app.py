"""
Global Fuel Prices and Taxation Trends - Fullstack Flask Web Application
Backend: Python 3 + Flask + SQLite 3 (with Pandas integration & stdlib fallback)
Features: Full REST API, CRUD operations, CSV/JSON export, statistical analytics,
          custom SQL calculated fields, and diagnostic benchmarks.
"""

from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, flash
import sqlite3
import csv
import io
import math
import time
from pathlib import Path

# Optional pandas import with graceful fallback
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fuel_prices.db"
CSV_PATH = BASE_DIR / "data" / "fuel_prices.csv"
SCHEMA_PATH = BASE_DIR / "schema.sql"

app = Flask(__name__)
app.secret_key = "fuel_prices_secret_key_prod_dev"


def get_connection():
    """Return an SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create tables, indexes, and views from schema.sql and seed from CSV if empty."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if SCHEMA_PATH.exists():
            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
            cursor.executescript(schema_sql)
        else:
            # Fallback inline schema if schema.sql missing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fuel_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country TEXT NOT NULL,
                    year INTEGER NOT NULL CHECK(year BETWEEN 1900 AND 2100),
                    fuel_type TEXT NOT NULL,
                    price_usd_per_litre REAL NOT NULL CHECK(price_usd_per_litre >= 0),
                    tax_percent REAL NOT NULL CHECK(tax_percent BETWEEN 0.0 AND 100.0),
                    currency TEXT DEFAULT 'USD',
                    source_note TEXT DEFAULT 'Official OECD/IEA & World Bank Series',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_country_year_fuel UNIQUE(country, year, fuel_type)
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_country ON fuel_prices(country);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_year ON fuel_prices(year);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_type ON fuel_prices(fuel_type);")

        # Check if table has data; if not, seed from CSV
        row_count = cursor.execute("SELECT COUNT(*) FROM fuel_prices").fetchone()[0]
        if row_count == 0 and CSV_PATH.exists():
            seed_database_from_csv(conn)


def seed_database_from_csv(conn=None):
    """Seed SQLite database from the bundled CSV file."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        if HAS_PANDAS:
            df = pd.read_csv(CSV_PATH)
            # Normalize column names
            df.columns = [c.strip().lower() for c in df.columns]
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO fuel_prices 
                    (country, year, fuel_type, price_usd_per_litre, tax_percent, currency, source_note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row["country"]).strip(),
                    int(row["year"]),
                    str(row["fuel_type"]).strip(),
                    float(row["price_usd_per_litre"]),
                    float(row["tax_percent"]),
                    str(row.get("currency", "USD")).strip(),
                    str(row.get("source_note", "Official Global Price Series")).strip()
                ))
        else:
            with open(CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute("""
                        INSERT OR REPLACE INTO fuel_prices 
                        (country, year, fuel_type, price_usd_per_litre, tax_percent, currency, source_note)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["country"].strip(),
                        int(row["year"]),
                        row["fuel_type"].strip(),
                        float(row["price_usd_per_litre"]),
                        float(row["tax_percent"]),
                        row.get("currency", "USD").strip(),
                        row.get("source_note", "Official Global Price Series").strip()
                    ))
        conn.commit()
    finally:
        if should_close:
            conn.close()


def get_filter_options():
    """Retrieve distinct countries, years, and fuel types for filter dropdowns."""
    with get_connection() as conn:
        cursor = conn.cursor()
        countries = [r[0] for r in cursor.execute(
            "SELECT DISTINCT country FROM fuel_prices ORDER BY country").fetchall()]
        years = [r[0] for r in cursor.execute(
            "SELECT DISTINCT year FROM fuel_prices ORDER BY year").fetchall()]
        fuel_types = [r[0] for r in cursor.execute(
            "SELECT DISTINCT fuel_type FROM fuel_prices ORDER BY fuel_type").fetchall()]
    return countries, years, fuel_types


def query_data(country=None, year=None, fuel_type=None, search=None,
               min_price=None, max_price=None, min_tax=None, max_tax=None,
               sort_by="year", sort_order="ASC", limit=None, offset=None):
    """
    Query fuel prices with dynamic filtering, calculated fields, sorting, and pagination.
    Calculated fields include:
      - estimated_tax_component: price * (tax_percent / 100)
      - estimated_pre_tax_component: price * (1 - tax_percent / 100)
      - tax_to_pretax_ratio: tax_percent / (100 - tax_percent)
    """
    sql = """
        SELECT 
            id,
            country,
            year,
            fuel_type,
            price_usd_per_litre,
            tax_percent,
            currency,
            source_note,
            ROUND(price_usd_per_litre * (tax_percent / 100.0), 3) AS estimated_tax_component,
            ROUND(price_usd_per_litre * (1.0 - (tax_percent / 100.0)), 3) AS estimated_pre_tax_component,
            ROUND(tax_percent / NULLIF(100.0 - tax_percent, 0), 3) AS tax_to_pretax_ratio
        FROM fuel_prices
        WHERE 1=1
    """
    params = []

    if country and country != "All":
        sql += " AND country = ?"
        params.append(country)

    if year and year != "All":
        try:
            sql += " AND year = ?"
            params.append(int(year))
        except (ValueError, TypeError):
            pass

    if fuel_type and fuel_type != "All":
        sql += " AND LOWER(fuel_type) = LOWER(?)"
        params.append(fuel_type)

    if search:
        sql += " AND (country LIKE ? OR source_note LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    if min_price is not None:
        try:
            sql += " AND price_usd_per_litre >= ?"
            params.append(float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price is not None:
        try:
            sql += " AND price_usd_per_litre <= ?"
            params.append(float(max_price))
        except (ValueError, TypeError):
            pass

    if min_tax is not None:
        try:
            sql += " AND tax_percent >= ?"
            params.append(float(min_tax))
        except (ValueError, TypeError):
            pass

    if max_tax is not None:
        try:
            sql += " AND tax_percent <= ?"
            params.append(float(max_tax))
        except (ValueError, TypeError):
            pass

    # Safe sorting column mapping
    valid_sort_cols = {
        "id": "id",
        "country": "country",
        "year": "year",
        "fuel_type": "fuel_type",
        "price_usd_per_litre": "price_usd_per_litre",
        "tax_percent": "tax_percent",
        "estimated_tax_component": "estimated_tax_component",
        "estimated_pre_tax_component": "estimated_pre_tax_component"
    }
    col = valid_sort_cols.get(sort_by, "year")
    direction = "DESC" if str(sort_order).upper() == "DESC" else "ASC"
    sql += f" ORDER BY {col} {direction}, country ASC, fuel_type ASC"

    if limit is not None:
        try:
            sql += " LIMIT ?"
            params.append(int(limit))
            if offset is not None:
                sql += " OFFSET ?"
                params.append(int(offset))
        except (ValueError, TypeError):
            pass

    with get_connection() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def calculate_pearson_correlation(rows):
    """Calculate Pearson correlation coefficient between tax_percent and price_usd_per_litre."""
    n = len(rows)
    if n < 2:
        return 0.0

    taxes = [float(r["tax_percent"]) for r in rows]
    prices = [float(r["price_usd_per_litre"]) for r in rows]

    mean_t = sum(taxes) / n
    mean_p = sum(prices) / n

    numerator = sum((t - mean_t) * (p - mean_p) for t, p in zip(taxes, prices))
    denom_t = sum((t - mean_t) ** 2 for t in taxes)
    denom_p = sum((p - mean_p) ** 2 for p in prices)

    denom = math.sqrt(denom_t * denom_p)
    if denom == 0:
        return 0.0
    return round(numerator / denom, 3)


# ====================================================================
# Web UI Routes
# ====================================================================

@app.route("/")
def index():
    """Main responsive dashboard view with interactive filters and charts."""
    initialize_database()
    countries, years, fuel_types = get_filter_options()

    selected_country = request.args.get("country", "All")
    selected_year = request.args.get("year", "All")
    selected_fuel = request.args.get("fuel_type", "All")
    search = request.args.get("search", "")

    rows = query_data(
        country=selected_country,
        year=selected_year,
        fuel_type=selected_fuel,
        search=search
    )

    return render_template(
        "index.html",
        countries=countries,
        years=years,
        fuel_types=fuel_types,
        rows=rows,
        selected_country=selected_country,
        selected_year=selected_year,
        selected_fuel=selected_fuel,
        search=search,
        tableau_url=""
    )


@app.route("/tableau")
def tableau():
    """Tableau dashboard embed page and interactive simulator."""
    tableau_url = request.args.get("url", "").strip()
    return render_template("tableau.html", tableau_url=tableau_url)


# ====================================================================
# RESTful API Endpoints
# ====================================================================

@app.route("/api/data")
def api_data():
    """Return JSON list of fuel price records matching optional query filters."""
    initialize_database()
    country = request.args.get("country")
    year = request.args.get("year")
    fuel_type = request.args.get("fuel_type")
    search = request.args.get("search")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    min_tax = request.args.get("min_tax")
    max_tax = request.args.get("max_tax")
    sort_by = request.args.get("sort_by", "year")
    sort_order = request.args.get("sort_order", "ASC")
    limit = request.args.get("limit")
    offset = request.args.get("offset")

    rows = query_data(
        country=country,
        year=year,
        fuel_type=fuel_type,
        search=search,
        min_price=min_price,
        max_price=max_price,
        min_tax=min_tax,
        max_tax=max_tax,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    return jsonify(rows)


@app.route("/api/summary")
def api_summary():
    """Return comprehensive summary metrics, aggregations, and correlation statistics."""
    initialize_database()
    country = request.args.get("country")
    year = request.args.get("year")
    fuel_type = request.args.get("fuel_type")
    search = request.args.get("search")

    rows = query_data(country=country, year=year, fuel_type=fuel_type, search=search)
    if not rows:
        return jsonify({
            "records": 0,
            "avg_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "avg_tax": 0.0,
            "min_tax": 0.0,
            "max_tax": 0.0,
            "countries": 0,
            "correlation": 0.0,
            "avg_tax_component": 0.0,
            "avg_pre_tax_component": 0.0,
            "petrol_avg": 0.0,
            "diesel_avg": 0.0
        })

    prices = [r["price_usd_per_litre"] for r in rows]
    taxes = [r["tax_percent"] for r in rows]
    tax_comps = [r["estimated_tax_component"] for r in rows]
    pretax_comps = [r["estimated_pre_tax_component"] for r in rows]
    unique_countries = {r["country"] for r in rows}

    petrol_prices = [r["price_usd_per_litre"] for r in rows if r["fuel_type"].lower() == "petrol"]
    diesel_prices = [r["price_usd_per_litre"] for r in rows if r["fuel_type"].lower() == "diesel"]

    correlation = calculate_pearson_correlation(rows)

    return jsonify({
        "records": len(rows),
        "avg_price": round(sum(prices) / len(prices), 3),
        "min_price": round(min(prices), 3),
        "max_price": round(max(prices), 3),
        "avg_tax": round(sum(taxes) / len(taxes), 2),
        "min_tax": round(min(taxes), 2),
        "max_tax": round(max(taxes), 2),
        "countries": len(unique_countries),
        "correlation": correlation,
        "avg_tax_component": round(sum(tax_comps) / len(tax_comps), 3),
        "avg_pre_tax_component": round(sum(pretax_comps) / len(pretax_comps), 3),
        "petrol_avg": round(sum(petrol_prices) / len(petrol_prices), 3) if petrol_prices else 0.0,
        "diesel_avg": round(sum(diesel_prices) / len(diesel_prices), 3) if diesel_prices else 0.0
    })


@app.route("/api/records", methods=["POST"])
def api_create_record():
    """Create a new fuel price record with backend validation."""
    initialize_database()
    data = request.get_json(silent=True) or request.form.to_dict()

    country = str(data.get("country", "")).strip()
    fuel_type = str(data.get("fuel_type", "Petrol")).strip()
    source_note = str(data.get("source_note", "User added record")).strip()
    currency = str(data.get("currency", "USD")).strip() or "USD"

    # Validation
    if not country:
        return jsonify({"error": "Country is required"}), 400

    try:
        year = int(data.get("year"))
        if not (1900 <= year <= 2100):
            return jsonify({"error": "Year must be between 1900 and 2100"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Valid integer year is required"}), 400

    try:
        price = float(data.get("price_usd_per_litre"))
        if price < 0:
            return jsonify({"error": "Price must be non-negative"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Valid price in USD is required"}), 400

    try:
        tax = float(data.get("tax_percent"))
        if not (0.0 <= tax <= 100.0):
            return jsonify({"error": "Tax percent must be between 0 and 100"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Valid tax percent between 0 and 100 is required"}), 400

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO fuel_prices 
                (country, year, fuel_type, price_usd_per_litre, tax_percent, currency, source_note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (country, year, fuel_type, price, tax, currency, source_note))
            conn.commit()
            new_id = cursor.lastrowid
            created = cursor.execute("SELECT * FROM fuel_prices WHERE id = ?", (new_id,)).fetchone()
            return jsonify({"success": True, "record": dict(created)}), 201
        except sqlite3.IntegrityError as e:
            return jsonify({"error": f"Record already exists for {country} ({year}, {fuel_type}): {str(e)}"}), 409


@app.route("/api/records/<int:record_id>", methods=["GET", "PUT", "DELETE"])
def api_record_detail(record_id):
    """Retrieve, update, or delete a single fuel price record."""
    initialize_database()

    if request.method == "GET":
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM fuel_prices WHERE id = ?", (record_id,)).fetchone()
            if not row:
                return jsonify({"error": "Record not found"}), 404
            return jsonify(dict(row))

    elif request.method == "PUT":
        data = request.get_json(silent=True) or request.form.to_dict()
        with get_connection() as conn:
            cursor = conn.cursor()
            existing = cursor.execute("SELECT * FROM fuel_prices WHERE id = ?", (record_id,)).fetchone()
            if not existing:
                return jsonify({"error": "Record not found"}), 404

            country = str(data.get("country", existing["country"])).strip()
            fuel_type = str(data.get("fuel_type", existing["fuel_type"])).strip()
            source_note = str(data.get("source_note", existing["source_note"])).strip()
            currency = str(data.get("currency", existing["currency"])).strip()

            try:
                year = int(data.get("year", existing["year"]))
                price = float(data.get("price_usd_per_litre", existing["price_usd_per_litre"]))
                tax = float(data.get("tax_percent", existing["tax_percent"]))
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid numeric values provided"}), 400

            if not (0.0 <= tax <= 100.0) or price < 0:
                return jsonify({"error": "Price must be >= 0 and tax between 0-100"}), 400

            cursor.execute("""
                UPDATE fuel_prices 
                SET country = ?, year = ?, fuel_type = ?, price_usd_per_litre = ?, 
                    tax_percent = ?, currency = ?, source_note = ?
                WHERE id = ?
            """, (country, year, fuel_type, price, tax, currency, source_note, record_id))
            conn.commit()
            updated = cursor.execute("SELECT * FROM fuel_prices WHERE id = ?", (record_id,)).fetchone()
            return jsonify({"success": True, "record": dict(updated)})

    elif request.method == "DELETE":
        with get_connection() as conn:
            cursor = conn.cursor()
            existing = cursor.execute("SELECT id FROM fuel_prices WHERE id = ?", (record_id,)).fetchone()
            if not existing:
                return jsonify({"error": "Record not found"}), 404
            cursor.execute("DELETE FROM fuel_prices WHERE id = ?", (record_id,))
            conn.commit()
            return jsonify({"success": True, "message": f"Record {record_id} deleted successfully"})


@app.route("/api/reset-db", methods=["POST"])
def api_reset_db():
    """Reset the database to initial clean state re-seeded from CSV."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS fuel_prices")
        conn.commit()
    initialize_database()
    return jsonify({"success": True, "message": "Database successfully reset and re-seeded from CSV."})


@app.route("/api/export/csv")
def export_csv():
    """Stream filtered records as a downloadable CSV file."""
    initialize_database()
    country = request.args.get("country")
    year = request.args.get("year")
    fuel_type = request.args.get("fuel_type")
    rows = query_data(country=country, year=year, fuel_type=fuel_type)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Country", "Year", "Fuel Type", "Price USD/Litre",
        "Tax Percent (%)", "Estimated Tax Component", "Estimated Pre-tax Component",
        "Tax to Pre-tax Ratio", "Currency", "Source Note"
    ])
    for r in rows:
        writer.writerow([
            r["id"], r["country"], r["year"], r["fuel_type"],
            r["price_usd_per_litre"], r["tax_percent"],
            r["estimated_tax_component"], r["estimated_pre_tax_component"],
            r["tax_to_pretax_ratio"], r["currency"], r["source_note"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=fuel_prices_export.csv"}
    )


@app.route("/api/export/json")
def export_json():
    """Stream filtered records as a downloadable JSON file."""
    initialize_database()
    country = request.args.get("country")
    year = request.args.get("year")
    fuel_type = request.args.get("fuel_type")
    rows = query_data(country=country, year=year, fuel_type=fuel_type)
    return jsonify({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "record_count": len(rows),
        "data": rows
    })


@app.route("/api/audit")
def api_audit():
    """Diagnostics and performance benchmark endpoint."""
    initialize_database()
    start_time = time.perf_counter()

    with get_connection() as conn:
        cursor = conn.cursor()
        # Row counts
        total_rows = cursor.execute("SELECT COUNT(*) FROM fuel_prices").fetchone()[0]

        # Integrity check
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]

        # Duplicate check
        dup_count = cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT country, year, fuel_type, COUNT(*) 
                FROM fuel_prices 
                GROUP BY country, year, fuel_type 
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        # Outlier count (negative price or tax not in 0-100)
        outlier_count = cursor.execute("""
            SELECT COUNT(*) FROM fuel_prices 
            WHERE price_usd_per_litre < 0 OR tax_percent < 0 OR tax_percent > 100
        """).fetchone()[0]

        # Distinct counts
        countries_count = cursor.execute("SELECT COUNT(DISTINCT country) FROM fuel_prices").fetchone()[0]
        years_count = cursor.execute("SELECT COUNT(DISTINCT year) FROM fuel_prices").fetchone()[0]

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return jsonify({
        "status": "healthy" if integrity == "ok" and dup_count == 0 else "warning",
        "integrity_check": integrity,
        "database_path": str(DB_PATH),
        "total_records": total_rows,
        "duplicates_detected": dup_count,
        "outliers_detected": outlier_count,
        "unique_countries": countries_count,
        "unique_years": years_count,
        "query_latency_ms": latency_ms,
        "pandas_available": HAS_PANDAS
    })


if __name__ == "__main__":
    import os
    initialize_database()
    port = int(os.environ.get("PORT", 5000))
    print(f" * Database initialized at: {DB_PATH}")
    print(f" * Starting Fuel Prices Analytics Fullstack App on http://0.0.0.0:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)
