-- ====================================================================
-- Global Fuel Prices and Taxation Trends - Database Schema & Analytics
-- Database: SQLite 3
-- ====================================================================

-- 1. Main Table with validation constraints and audit defaults
CREATE TABLE IF NOT EXISTS fuel_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT NOT NULL,
    year INTEGER NOT NULL CHECK(year BETWEEN 1900 AND 2100),
    fuel_type TEXT NOT NULL CHECK(fuel_type IN ('Petrol', 'Diesel', 'petrol', 'diesel', 'Electric', 'Hybrid', 'LPG', 'CNG', 'Other')),
    price_usd_per_litre REAL NOT NULL CHECK(price_usd_per_litre >= 0),
    tax_percent REAL NOT NULL CHECK(tax_percent BETWEEN 0.0 AND 100.0),
    currency TEXT DEFAULT 'USD',
    source_note TEXT DEFAULT 'Official OECD/IEA & World Bank Global Fuel Price Series',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_country_year_fuel UNIQUE(country, year, fuel_type)
);

-- 2. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_fuel_country ON fuel_prices(country);
CREATE INDEX IF NOT EXISTS idx_fuel_year ON fuel_prices(year);
CREATE INDEX IF NOT EXISTS idx_fuel_type ON fuel_prices(fuel_type);
CREATE INDEX IF NOT EXISTS idx_fuel_compound ON fuel_prices(country, year, fuel_type);

-- 3. Analytical View: Calculated Decomposition & Tax Brackets
CREATE VIEW IF NOT EXISTS v_fuel_analytics AS
SELECT 
    id,
    country,
    year,
    fuel_type,
    price_usd_per_litre,
    tax_percent,
    currency,
    source_note,
    ROUND(price_usd_per_litre * (tax_percent / 100.0), 4) AS estimated_tax_component,
    ROUND(price_usd_per_litre * (1.0 - (tax_percent / 100.0)), 4) AS estimated_pre_tax_component,
    ROUND(tax_percent / NULLIF(100.0 - tax_percent, 0), 4) AS tax_to_pretax_ratio,
    CASE 
        WHEN tax_percent >= 50.0 THEN 'High (>50%)'
        WHEN tax_percent >= 30.0 THEN 'Moderate (30-50%)'
        ELSE 'Low (<30%)'
    END AS tax_bracket
FROM fuel_prices;

-- 4. Analytical View: Country Aggregate Summary
CREATE VIEW IF NOT EXISTS v_country_summary AS
SELECT 
    country,
    COUNT(*) AS total_records,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    ROUND(AVG(price_usd_per_litre), 3) AS avg_price,
    ROUND(MIN(price_usd_per_litre), 3) AS min_price,
    ROUND(MAX(price_usd_per_litre), 3) AS max_price,
    ROUND(AVG(tax_percent), 2) AS avg_tax_percent,
    ROUND(AVG(price_usd_per_litre * (tax_percent / 100.0)), 3) AS avg_tax_component,
    ROUND(AVG(price_usd_per_litre * (1.0 - (tax_percent / 100.0))), 3) AS avg_pretax_component
FROM fuel_prices
GROUP BY country;

-- 5. Analytical View: Year Trends with Petrol vs Diesel Decomposition
CREATE VIEW IF NOT EXISTS v_year_trends AS
SELECT 
    year,
    COUNT(*) AS records_count,
    ROUND(AVG(price_usd_per_litre), 3) AS avg_overall_price,
    ROUND(AVG(CASE WHEN LOWER(fuel_type) = 'petrol' THEN price_usd_per_litre END), 3) AS avg_petrol_price,
    ROUND(AVG(CASE WHEN LOWER(fuel_type) = 'diesel' THEN price_usd_per_litre END), 3) AS avg_diesel_price,
    ROUND(AVG(tax_percent), 2) AS avg_tax_rate
FROM fuel_prices
GROUP BY year
ORDER BY year;

-- ====================================================================
-- Benchmark & Verification Queries
-- ====================================================================

-- Query A: Year-over-Year price change using SQL Window Functions
-- SELECT year, avg_overall_price,
--        ROUND(avg_overall_price - LAG(avg_overall_price) OVER (ORDER BY year), 3) AS yoy_change_usd,
--        ROUND(((avg_overall_price - LAG(avg_overall_price) OVER (ORDER BY year)) / LAG(avg_overall_price) OVER (ORDER BY year)) * 100.0, 2) AS yoy_growth_pct
-- FROM v_year_trends;

-- Query B: Data Integrity & Duplicate Check (Should return 0 rows)
-- SELECT country, year, fuel_type, COUNT(*) AS count
-- FROM fuel_prices
-- GROUP BY country, year, fuel_type
-- HAVING COUNT(*) > 1;

-- Query C: Outlier and Range Sanity Check (Should return 0 rows)
-- SELECT * FROM fuel_prices
-- WHERE price_usd_per_litre < 0 OR tax_percent < 0 OR tax_percent > 100;
