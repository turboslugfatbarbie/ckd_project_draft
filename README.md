# CKD Green Space Policy Simulator

**CSE 6242 Visual Analytics — Team 059 | Georgia Institute of Technology**

An interactive policy simulation tool that models the relationship between urban green space investment and projected Chronic Kidney Disease (CKD) prevalence across U.S. counties. Built on a Gradient Boosting Regressor trained on EPA and CDC environmental and health data (2018–2020).

---

## Overview

This tool allows researchers and policymakers to:

- Simulate the effect of increasing urban green space (measured by NDVI) on county-level CKD risk
- Translate abstract green space percentages into concrete policy actions (tree planting, parking lot conversion)
- Explore multi-factor environmental interventions including PM2.5 reduction, traffic exposure, and income investment
- Browse county-level CKD and environmental data across all U.S. states

---

## Installation

**Requirements:** Python 3.9+

```bash
cd project_model
pip install streamlit geopandas plotly pandas numpy streamlit-option-menu statsmodels
```

**Run the app:**

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Project Structure

```
project_model/
│
├── app.py                  # Main Streamlit application
├── simulation.py           # Simulation engine (green space + multi-factor)
├── data_loader.py          # Cached data loading and county aggregation
│
├── Data/
│   ├── CKD_Predictions.csv         # Model predictions + pre-computed scenarios
│   ├── Final_Visual_Data.geojson   # Census tract geometry with environmental data
│   └── MASTER_with_Full_SVI.csv    # Master dataset with Social Vulnerability Index
│
├── CITATIONS_NEEDED.md     # Reference tracker for all factual claims in the UI
└── README.md               # This file
```

---

## Data

### CKD_Predictions.csv

County-level model output. Key columns:

| Column | Description |
|---|---|
| `GEOID` | 11-digit Census tract identifier |
| `CKD_Prevalence` | Observed CKD rate (%), CDC PLACES 2018–2020 |
| `Predicted_CKD` | Model-predicted CKD rate (%) |
| `Risk_Level` | Derived classification: Low / Medium / High |
| `Green_Space_Index` | NDVI score (0–1) for the tract |
| `PM25` | Annual mean PM2.5 concentration (μg/m³) |
| `OZONE` | Ground-level ozone (ppb) |
| `PTRAF` | EPA EJScreen traffic proximity index |
| `LOWINCPCT` | Share of population at or below 200% federal poverty level |
| `Percent_Age_65plus` | Share of population aged 65 or older |
| `Percent_Uninsured` | Share of population without health insurance |
| `Predicted_CKD_0pct_increase` | Model prediction at current NDVI (baseline) |
| `Predicted_CKD_10pct_increase` | Model prediction at +10% NDVI |
| `Predicted_CKD_20pct_increase` | Model prediction at +20% NDVI |
| `Predicted_CKD_50pct_increase` | Model prediction at +50% NDVI |
| `Predicted_CKD_100pct_increase` | Model prediction at +100% NDVI |

### Final_Visual_Data.geojson

Census tract geometries joined with environmental variables. Used to build county-level choropleth maps.

---

## Application Pages

### Green Space Simulator
The primary interface. Adjust the **Green Space Increase (%)** slider in the left panel to simulate NDVI investment across all U.S. counties. Displays:
- Key metrics (baseline CKD, simulated CKD, counties improving, population benefiting)
- Benefit map showing projected CKD reduction by county
- Side-by-side baseline vs. simulated risk maps
- Collapsible risk shift chart and top-15 county table

The slider uses **pre-computed model predictions** at 0%, 10%, 20%, 50%, and 100% NDVI increase, linearly interpolated to the selected value. This ensures estimates reflect actual model outputs rather than heuristic approximations.

### Multi-Factor Analysis
Extends the simulator with additional environmental and socioeconomic policy levers: PM2.5 reduction, traffic exposure reduction, and low-income population reduction. Includes a factor contribution bar chart. Secondary effect sizes are approximate — see `CITATIONS_NEEDED.md`.

### County Explorer
State-filtered geographic explorer. Select one or more states to zoom the choropleth map, view a Green Space Index vs. CKD prevalence scatter plot with OLS trendline, and download filtered county data as CSV.

### Glossary
Plain-language definitions of all technical, environmental, and statistical terms used in the tool, written for a policy and public health audience.

---

## Sidebar Tools

The left panel (visible on all pages) provides:

- **Green Space Increase (%)** — primary simulation slider (0–100%)
- **Tree Planting Estimator** — estimates trees needed per acre / sq mile / 100 sq mi city to achieve the selected NDVI increase, for three tree sizes (small, medium, large by caliper)
- **Parking Lot Converter** — estimates standard parking spaces (8.5 × 18 ft) to convert to vegetated ground cover to achieve the same increase
- **Export Report** — generates a formatted plain-text scenario report with toggleable sections (health impact, tree estimates, parking estimates, top 10 counties)

---

## Model

The underlying model is a **Gradient Boosting Regressor** trained to predict county-level CKD prevalence from the following features:

- Green Space Index (NDVI)
- PM2.5 concentration
- Ozone (OZONE)
- Traffic proximity (PTRAF)
- Low-income percentage (LOWINCPCT)
- Average maximum temperature
- Percent population aged 65+
- Percent uninsured

**Performance on held-out test set:** R² = 0.44, Mean Absolute Error ≈ 0.39 percentage points.

Pre-computed predictions at five NDVI scenarios (0%, 10%, 20%, 50%, 100% increase) are stored directly in `CKD_Predictions.csv` and interpolated by the simulation engine at runtime.

---

## Citations & References

All factual claims made in the app UI — including NDVI definitions, health pathway descriptions, policy analogies, and tree/parking estimation assumptions — are tracked in `CITATIONS_NEEDED.md` with their verification status and recommended primary sources.

**Key sources:**
- CDC PLACES: Local Data for Better Health — county-level CKD prevalence
- EPA EJScreen Environmental Justice Screening Tool — PM2.5, PTRAF, LOWINCPCT
- EPA EnviroAtlas — NDVI-derived green space metrics
- ANSI Z60.1 — Nursery stock standards (tree caliper definitions)
- i-Tree Tools (USDA Forest Service) — urban tree canopy metrics

---

## Notes & Limitations

- Data covers **2018–2020** and is averaged across years for model training. Predictions reflect conditions during that period and should not be extrapolated to current conditions without retraining.
- The simulation assumes green space interventions are implemented on **currently impervious surfaces**. Planting on existing vegetation would yield smaller NDVI gains.
- Tree and parking lot estimates assume **mature canopy** (reached ~10–15 years post-planting). Newly planted trees will contribute less NDVI in the short term.
- County-level aggregation from census tract data involves averaging; within-county variation is not captured.
- Secondary factor coefficients in the Multi-Factor Analysis tab are approximate. Do not cite these for formal policy analysis without deriving values from the model's feature importances.
