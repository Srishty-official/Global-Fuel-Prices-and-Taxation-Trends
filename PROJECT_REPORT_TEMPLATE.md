# Project Report: Global Fuel Prices and Taxation Trends

## Abstract
This project explores differences and changes in fuel prices and tax rates across countries, years, and fuel types using a database-backed dashboard. The included demo data is illustrative; final conclusions must be based on verified sourced data.

## Problem Statement
Fuel prices vary between countries and over time. The project organizes fuel-price and tax data to compare trends and explore possible associations.

## Objectives
- Store and query fuel-price observations in SQLite.
- Use SQL and calculated fields to summarize price and taxation.
- Visualize time trends, country comparisons, and price-tax relationships.
- Provide interactive filters and a web dashboard.
- Optionally embed a published Tableau dashboard/story in Flask.

## Tools
Python, Flask, Pandas, SQLite, HTML/CSS, Chart.js, Tableau (optional).

## Dataset
Document the actual publisher, source URL, retrieval date, time period, units, tax definitions, license, and missing-value handling. Do not present the included illustrative values as official data.

## Methodology
1. Define the research question.
2. Collect and verify source data.
3. Normalize country labels, years, currency, units, and tax definitions.
4. Load data into SQLite.
5. Run aggregation and validation queries.
6. Build three charts and filters.
7. Create dashboard/story.
8. Test accuracy, responsiveness, and performance.

## Calculated Fields
- Estimated tax component = retail price × tax percent ÷ 100.
- Estimated pre-tax component = retail price × (1 − tax percent ÷ 100).
These are valid only if the tax percentage represents the share of retail price.

## Visualizations
1. Line chart: average price by year.
2. Bar chart: average tax rate by country.
3. Scatter plot: tax percentage vs retail price.

## Testing
Record imported row count, duplicate count, missing values, filter test results, browser sizes tested, and load time. Include screenshots from your final application.

## Results and Discussion
Complete this section after replacing the demo dataset. Explain the trends visible in the real data and avoid causal claims unless supported by an appropriate analysis.

## Limitations
Country-level data can differ in definitions, regional variation, tax treatment, currency conversion, and reporting dates. Correlation does not establish causation.

## Conclusion
Summarize evidence-based findings from the verified dataset and identify improvements.

## Demo video script
Introduce the project; show the dataset and source; demonstrate database and SQL; walk through each chart and filter; show Tableau integration if configured; finish with validation, limitations, and conclusion.
