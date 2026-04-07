"""
CKD Green Space Policy Simulator
Team 059 — CSE 6242 Visual Analytics, Georgia Tech

Run with:
    cd project_model
    pip install streamlit geopandas plotly pandas numpy streamlit-option-menu statsmodels
    streamlit run app.py
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu

from data_loader import load_county_data
from simulation import simulate_greenspace, simulate_multifactor

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CKD Green Space Policy Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CDC-style design system ───────────────────────────────────────────────────
CDC_NAVY   = "#003f72"
CDC_BLUE   = "#0071bc"
CDC_GREEN  = "#1a9c3e"
CDC_RED    = "#d63524"
CDC_AMBER  = "#e07b00"
CDC_LIGHT  = "#f5f7fa"
CDC_WHITE  = "#ffffff"
CDC_BORDER = "#dde1e7"
CDC_TEXT   = "#212121"
CDC_MUTED  = "#5a6472"

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2}
RISK_COLORSCALE = [
    [0.00, "#1a9c3e"], [0.33, "#1a9c3e"],
    [0.33, CDC_AMBER],  [0.66, CDC_AMBER],
    [0.66, CDC_RED],    [1.00, CDC_RED],
]
RISK_COLORS = {"High": CDC_RED, "Medium": CDC_AMBER, "Low": CDC_GREEN}

MEAN_NDVI       = 0.22
NDVI_BOOST_TREE = 0.60
NDVI_BOOST_PARK = 0.35
PARKING_SQM     = 14.2
SQM_PER_ACRE    = 4_047
SQM_PER_SQ_MILE = 2_589_988

TREE_SIZE_MAP = {
    'Small  (1–2" caliper, ~10 ft canopy)':  (20,  '1–2"',  '~10 ft'),
    'Medium (4–6" caliper, ~25 ft canopy)':  (50,  '4–6"',  '~25 ft'),
    'Large  (8–12" caliper, ~45 ft canopy)': (120, '8–12"', '~45 ft'),
}

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Remove Streamlit chrome ── */
#MainMenu, footer, header[data-testid="stHeader"] {{ display: none !important; }}
.stDeployButton {{ display: none; }}

/* ── Page background ── */
.stApp {{ background-color: {CDC_LIGHT}; }}
.main .block-container {{
    padding-top: 0 !important;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: {CDC_NAVY} !important;
    min-width: 220px !important;
    max-width: 220px !important;
    border-right: 3px solid {CDC_BLUE};
}}
[data-testid="stSidebar"] > div:first-child {{
    width: 220px !important;
    padding-top: 1.2rem;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
    color: #c8ddf0 !important;
    font-size: 11.5px;
    line-height: 1.65;
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b {{
    color: #ffffff !important;
}}
[data-testid="stSidebar"] label {{
    color: #c8ddf0 !important;
    font-size: 11.5px !important;
}}
[data-testid="stSidebar"] hr {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.12) !important;
    margin: 10px 0;
}}
[data-testid="stSidebar"] table {{
    color: #c8ddf0 !important;
    font-size: 11px !important;
    width: 100%;
    border-collapse: collapse;
}}
[data-testid="stSidebar"] table td,
[data-testid="stSidebar"] table th {{
    border-color: rgba(255,255,255,0.08) !important;
    padding: 3px 5px !important;
}}
[data-testid="stSidebar"] .stDownloadButton button {{
    background-color: {CDC_BLUE} !important;
    color: white !important;
    border: none !important;
    border-radius: 3px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    width: 100%;
    padding: 8px 0 !important;
}}
[data-testid="stSidebar"] .stDownloadButton button:hover {{
    background-color: #005a9e !important;
}}
[data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {{
    background-color: {CDC_BLUE} !important;
    color: white !important;
}}
[data-testid="stSidebar"] .stCheckbox label p {{
    color: #c8ddf0 !important;
    font-size: 11.5px !important;
}}

/* ── Banner ── */
.site-banner {{
    background: {CDC_NAVY};
    padding: 16px 0 12px;
    margin: -0.5rem -2rem 0;
    border-bottom: 3px solid {CDC_BLUE};
}}
.banner-inner {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 0 2rem;
}}
.banner-title {{
    color: white;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.3px;
    line-height: 1.2;
}}
.banner-sub {{
    color: #90bde0;
    font-size: 11.5px;
    margin-top: 4px;
    letter-spacing: 0.2px;
}}
.banner-meta {{
    color: #7aafd4;
    font-size: 11px;
    text-align: right;
    line-height: 1.7;
}}

/* ── Nav bar (option_menu overrides) ── */
div[data-testid="stHorizontalBlock"] > div:first-child {{
    padding: 0;
}}

/* ── Metric cards ── */
.stat-card {{
    background: {CDC_WHITE};
    border-radius: 3px;
    padding: 14px 16px;
    border-top: 4px solid {CDC_BLUE};
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    text-align: center;
    height: 100%;
}}
.stat-card.green  {{ border-top-color: {CDC_GREEN}; }}
.stat-card.red    {{ border-top-color: {CDC_RED}; }}
.stat-card.amber  {{ border-top-color: {CDC_AMBER}; }}
.stat-label {{
    color: {CDC_MUTED};
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
    margin-bottom: 6px;
}}
.stat-value {{
    font-size: 22px;
    font-weight: 700;
    color: {CDC_NAVY};
    line-height: 1.1;
}}
.stat-delta {{
    font-size: 11.5px;
    margin-top: 5px;
    font-weight: 600;
}}

/* ── Section headers ── */
.section-header {{
    color: {CDC_NAVY};
    font-size: 16px;
    font-weight: 700;
    border-bottom: 2px solid {CDC_BORDER};
    padding-bottom: 6px;
    margin: 1.2rem 0 0.8rem;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
    background: {CDC_WHITE};
    border: 1px solid {CDC_BORDER};
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
details summary p {{
    font-weight: 600 !important;
    color: {CDC_NAVY} !important;
}}

/* ── Divider ── */
hr {{ border-color: {CDC_BORDER} !important; }}

/* ── Info box ── */
[data-testid="stInfo"] {{
    background-color: #e8f2fb;
    border-left: 4px solid {CDC_BLUE};
    border-radius: 0 3px 3px 0;
    color: {CDC_TEXT};
}}

/* ── Tables ── */
[data-testid="stDataFrame"] {{
    border-radius: 3px;
    border: 1px solid {CDC_BORDER};
}}
thead tr th {{
    background-color: {CDC_NAVY} !important;
    color: white !important;
}}

/* ── Download buttons (main area) ── */
.stDownloadButton button {{
    background-color: {CDC_WHITE} !important;
    color: {CDC_NAVY} !important;
    border: 1px solid {CDC_BLUE} !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
.stDownloadButton button:hover {{
    background-color: #e8f2fb !important;
}}

/* ── Plotly chart container ── */
.stPlotlyChart {{
    background: {CDC_WHITE};
    border-radius: 3px;
    border: 1px solid {CDC_BORDER};
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

/* ── Glossary terms ── */
.term-name {{
    color: {CDC_NAVY};
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 4px;
}}
.term-def {{
    color: {CDC_TEXT};
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 4px;
}}
.term-example {{
    color: {CDC_MUTED};
    font-size: 12px;
    font-style: italic;
    border-left: 3px solid {CDC_BLUE};
    padding-left: 10px;
    margin-top: 4px;
}}
.term-divider {{
    border: none;
    border-top: 1px solid {CDC_BORDER};
    margin: 12px 0;
}}
</style>
""", unsafe_allow_html=True)


# ── Map builders ──────────────────────────────────────────────────────────────
def build_choropleth(df, geojson_data, risk_col, ckd_col, title):
    df = df.copy()
    df["_risk_num"] = df[risk_col].map(RISK_ORDER).fillna(1)
    fig = go.Figure(go.Choropleth(
        geojson=geojson_data,
        locations=df.index,
        z=df["_risk_num"],
        colorscale=RISK_COLORSCALE,
        zmin=0, zmax=2,
        marker_line_width=0.3,
        marker_line_color="white",
        colorbar=dict(
            tickvals=[0.33, 1.0, 1.66],
            ticktext=["Low", "Medium", "High"],
            thickness=12, len=0.55,
            title=dict(text="CKD Risk", font=dict(size=11)),
        ),
        hovertemplate=(
            "<b>%{customdata[0]}, %{customdata[1]}</b><br>"
            "Risk Level: %{customdata[2]}<br>"
            "Predicted CKD: %{customdata[3]:.2f}%<br>"
            "Green Space Index: %{customdata[4]:.3f}<br>"
            "Population: %{customdata[5]:,.0f}<br>"
            "<extra></extra>"
        ),
        customdata=df[["COUNTY_FIPS", "State_Name", risk_col,
                        ckd_col, "Green_Space_Index", "Population"]].values,
    ))
    fig.update_geos(scope="usa", showland=True, landcolor="#f0f4f8",
                    showlakes=True, lakecolor="#c8d8e8",
                    showcoastlines=True, coastlinecolor="#aaaaaa", showframe=False)
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=CDC_NAVY, family="sans-serif"), x=0.5),
        margin=dict(l=0, r=0, t=38, b=0),
        height=430,
        paper_bgcolor=CDC_WHITE,
    )
    return fig


def build_state_choropleth(df, risk_col, ckd_col, title):
    df = df.copy().reset_index(drop=True)
    df["_risk_num"] = df[risk_col].map(RISK_ORDER).fillna(1)
    geojson_state = df.__geo_interface__
    fig = go.Figure(go.Choropleth(
        geojson=geojson_state,
        locations=df.index,
        z=df["_risk_num"],
        colorscale=RISK_COLORSCALE,
        zmin=0, zmax=2,
        marker_line_width=0.5,
        marker_line_color="white",
        colorbar=dict(
            tickvals=[0.33, 1.0, 1.66],
            ticktext=["Low", "Medium", "High"],
            thickness=12, len=0.55,
            title=dict(text="CKD Risk", font=dict(size=11)),
        ),
        hovertemplate=(
            "<b>%{customdata[0]}, %{customdata[1]}</b><br>"
            "Risk Level: %{customdata[2]}<br>"
            "CKD Prevalence: %{customdata[3]:.2f}%<br>"
            "Green Space Index: %{customdata[4]:.3f}<br>"
            "Population: %{customdata[5]:,.0f}<br>"
            "<extra></extra>"
        ),
        customdata=df[["COUNTY_FIPS", "State_Name", risk_col,
                        ckd_col, "Green_Space_Index", "Population"]].values,
    ))
    fig.update_geos(fitbounds="locations", visible=True,
                    showland=True, landcolor="#f0f4f8",
                    showlakes=True, lakecolor="#c8d8e8",
                    showcoastlines=True, coastlinecolor="#aaaaaa", showframe=False)
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=CDC_NAVY), x=0.5),
        margin=dict(l=0, r=0, t=38, b=0),
        height=460,
        paper_bgcolor=CDC_WHITE,
    )
    return fig


def build_delta_map(df, geojson_data):
    df = df.copy()
    df["_delta"] = df["Predicted_CKD"] - df["Simulated_CKD"]
    fig = go.Figure(go.Choropleth(
        geojson=geojson_data,
        locations=df.index,
        z=df["_delta"],
        colorscale=[[0, "#e8f5e9"], [0.5, "#43a047"], [1, "#1b5e20"]],
        zmin=0,
        zmax=df["_delta"].quantile(0.95),
        marker_line_width=0.3,
        marker_line_color="white",
        colorbar=dict(
            thickness=12, len=0.55,
            title=dict(text="CKD Drop (pp)", font=dict(size=11)),
        ),
        hovertemplate=(
            "<b>%{customdata[0]}, %{customdata[1]}</b><br>"
            "CKD Reduction: %{customdata[2]:.3f} pp<br>"
            "Green Space Index: %{customdata[3]:.3f}<br>"
            "<extra></extra>"
        ),
        customdata=df[["COUNTY_FIPS", "State_Name", "_delta", "Green_Space_Index"]].values,
    ))
    fig.update_geos(scope="usa", showland=True, landcolor="#f0f4f8",
                    showlakes=True, lakecolor="#c8d8e8", showframe=False)
    fig.update_layout(
        title=dict(text="Projected CKD Reduction by County — Darker Indicates Greater Benefit",
                   font=dict(size=13, color=CDC_NAVY), x=0.5),
        margin=dict(l=0, r=0, t=38, b=0),
        height=430,
        paper_bgcolor=CDC_WHITE,
    )
    return fig


# ── Metric cards ──────────────────────────────────────────────────────────────
def render_stats(sim):
    baseline    = sim["Predicted_CKD"].mean()
    simulated   = sim["Simulated_CKD"].mean()
    delta       = simulated - baseline
    shifted     = (sim["Simulated_Risk"] != sim["Risk_Level"]).sum()
    pop_benefit = sim.loc[sim["Simulated_Risk"] != sim["Risk_Level"], "Population"].sum()

    delta_color  = CDC_GREEN if delta < 0 else CDC_RED
    delta_sign   = "▼" if delta < 0 else "▲"
    delta_label  = f'{delta_sign} {abs(delta):.3f} percentage points'

    cards = [
        ("Baseline Predicted CKD", f"{baseline:.2f}%", "", CDC_BLUE, ""),
        ("Simulated CKD", f"{simulated:.2f}%", delta_label, delta_color,
         "green" if delta < 0 else "red"),
        ("Counties Improving", f"{shifted:,}", "", CDC_GREEN, "green"),
        ("Population Benefiting", f"{pop_benefit/1e6:.1f}M", "", CDC_GREEN, "green"),
        ("Model R²", "0.44", "Gradient Boosting Regressor", CDC_BLUE, ""),
    ]

    cols = st.columns(5)
    for col, (label, value, sub, color, accent) in zip(cols, cards):
        sub_html = (f'<div class="stat-delta" style="color:{color}">{sub}</div>'
                    if sub else "")
        col.markdown(f"""
        <div class="stat-card {accent}">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            {sub_html}
        </div>""", unsafe_allow_html=True)

    return delta, shifted


def _section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────────
county_gdf = load_county_data()
geojson    = county_gdf.__geo_interface__


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — Simulation Parameters
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## Simulation Parameters")
    st.markdown("---")

    greenspace_pct = st.slider(
        "Green Space Increase (%)",
        min_value=0, max_value=100, value=10, step=1,
        help="Increases each county's NDVI by the selected percentage and shows the model's predicted impact on CKD rates."
    )
    st.markdown("---")

    st.markdown(
        "The **Green Space Index** is derived from NDVI (Normalized Difference "
        "Vegetation Index), a satellite measure of vegetation density scaled from "
        "0.0 (impervious surface) to 1.0 (dense canopy). The study average across "
        "U.S. counties is **0.22**."
    )
    st.markdown(
        "Peer-reviewed literature associates green space expansion with reductions "
        "in ambient particulate matter, urban heat, and physiological stress — "
        "environmental pathways independently linked to hypertension and diabetes, "
        "the two primary antecedents of CKD."
    )
    st.markdown("---")

    # Tree Planting Estimator
    st.markdown("#### Tree Planting Estimator")
    st.markdown("Estimated trees required per unit area to achieve the selected increase:")

    tree_label = st.selectbox(
        "Tree size",
        options=list(TREE_SIZE_MAP.keys()),
        index=1,
        help="Caliper = trunk diameter at 6\" above ground (ANSI Z60.1). Canopy size reflects mature spread, typically 10–15 years post-planting. Estimates assume replacement of impervious surfaces."
    )
    canopy_sqm, caliper, canopy_diam = TREE_SIZE_MAP[tree_label]
    delta_ndvi = MEAN_NDVI * (greenspace_pct / 100)

    if greenspace_pct > 0:
        trees_per_acre = (delta_ndvi * SQM_PER_ACRE)    / (NDVI_BOOST_TREE * canopy_sqm)
        trees_per_sqmi = (delta_ndvi * SQM_PER_SQ_MILE) / (NDVI_BOOST_TREE * canopy_sqm)
        st.markdown(
            f"| | |\n|---|---|\n"
            f"| Per acre | **~{trees_per_acre:.1f}** |\n"
            f"| Per sq mile | **~{trees_per_sqmi:,.0f}** |\n"
            f"| Per 100 sq mi city | **~{trees_per_sqmi*100:,.0f}** |"
        )
        st.markdown(f"*{caliper} caliper · {canopy_diam} canopy · matures ~10–15 yrs*")
    else:
        st.markdown("*Adjust the slider above to view estimates.*")

    st.markdown("---")

    # Parking Lot Converter
    st.markdown("#### Parking Lot Converter")
    st.markdown(
        "Standard spaces (8.5 × 18 ft, ~14.2 m²) to convert to vegetated "
        "ground cover (grass, bioswales, permeable pavers):"
    )

    if greenspace_pct > 0:
        spaces_per_acre = (delta_ndvi * SQM_PER_ACRE)    / (NDVI_BOOST_PARK * PARKING_SQM)
        spaces_per_sqmi = (delta_ndvi * SQM_PER_SQ_MILE) / (NDVI_BOOST_PARK * PARKING_SQM)
        st.markdown(
            f"| | |\n|---|---|\n"
            f"| Per acre | **~{spaces_per_acre:.1f}** |\n"
            f"| Per sq mile | **~{spaces_per_sqmi:,.0f}** |\n"
            f"| Per 100 sq mi city | **~{spaces_per_sqmi*100:,.0f}** |"
        )
        st.markdown("*Asphalt NDVI ~0.05 → vegetated surface NDVI ~0.40*")
    else:
        st.markdown("*Adjust the slider above to view estimates.*")

    st.markdown("---")
    st.markdown("*Parameters apply to the Green Space Simulator.*")

# ── Run simulation ─────────────────────────────────────────────────────────────
sim        = simulate_greenspace(county_gdf, greenspace_pct)
delta_ndvi = MEAN_NDVI * (greenspace_pct / 100)

# ── Second sidebar block: export (after sim is computed) ───────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("#### Export Scenario Report")
    st.markdown("Select sections to include:")

    rpt_health   = st.checkbox("Health Impact Summary",   value=True)
    rpt_trees    = st.checkbox("Tree Planting Estimates", value=True)
    rpt_parking  = st.checkbox("Parking Lot Estimates",   value=True)
    rpt_counties = st.checkbox("Top 10 Counties",         value=True)

    def _build_report():
        from datetime import datetime
        L = []
        L += [
            "=" * 60,
            "CKD GREEN SPACE POLICY SIMULATOR — SCENARIO REPORT",
            f"Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "Project:    CSE 6242 Visual Analytics — Team 059",
            "           Georgia Institute of Technology",
            "=" * 60,
            "",
            "SCENARIO PARAMETERS",
            "-" * 40,
            f"  Green Space Index Increase:  {greenspace_pct}%",
            f"  Mean county NDVI (baseline): {MEAN_NDVI:.2f}",
            f"  Mean county NDVI (scenario): {MEAN_NDVI*(1+greenspace_pct/100):.3f}",
            "",
        ]

        if rpt_health:
            bl  = sim["Predicted_CKD"].mean()
            sv  = sim["Simulated_CKD"].mean()
            dv  = sv - bl
            sh  = (sim["Simulated_Risk"] != sim["Risk_Level"]).sum()
            pop = sim.loc[sim["Simulated_Risk"] != sim["Risk_Level"], "Population"].sum()
            rc  = sim["Simulated_Risk"].value_counts()
            L += [
                "HEALTH IMPACT SUMMARY",
                "-" * 40,
                f"  Baseline predicted CKD rate:  {bl:.2f}%",
                f"  Simulated CKD rate:           {sv:.2f}%",
                f"  Net change:                   {dv:+.3f} percentage points",
                f"  Counties improving risk level: {sh:,}",
                f"  Estimated population benefit:  {pop/1e6:.1f}M",
                "",
                "  Simulated risk distribution:",
                f"    Low:    {rc.get('Low', 0):,} counties",
                f"    Medium: {rc.get('Medium', 0):,} counties",
                f"    High:   {rc.get('High', 0):,} counties",
                "",
                "  Model: Gradient Boosting Regressor",
                "  R² = 0.44 (held-out test set) | MAE ~0.39%",
                "  Data: EPA / CDC PLACES, 2018–2020 average",
                "",
            ]

        if rpt_trees and greenspace_pct > 0:
            tpa  = (delta_ndvi * SQM_PER_ACRE)    / (NDVI_BOOST_TREE * canopy_sqm)
            tpmi = (delta_ndvi * SQM_PER_SQ_MILE) / (NDVI_BOOST_TREE * canopy_sqm)
            L += [
                "TREE PLANTING ESTIMATES",
                "-" * 40,
                f"  Tree size selected:       {tree_label}",
                f"  Trunk caliper:            {caliper}",
                f"  Mature canopy diameter:   {canopy_diam}",
                f"  Canopy area:              {canopy_sqm} m²",
                f"  Time to mature canopy:    ~10–15 years post-planting",
                "",
                f"  Trees required per acre:         ~{tpa:.1f}",
                f"  Trees required per sq mile:      ~{tpmi:,.0f}",
                f"  Trees required per 100 sq mi:    ~{tpmi*100:,.0f}",
                "",
                "  Methodology: replaces impervious surface (NDVI ~0.05) with",
                "  mature canopy (NDVI ~0.65); net NDVI gain of 0.60 per m².",
                "",
            ]

        if rpt_parking and greenspace_pct > 0:
            spa  = (delta_ndvi * SQM_PER_ACRE)    / (NDVI_BOOST_PARK * PARKING_SQM)
            spmi = (delta_ndvi * SQM_PER_SQ_MILE) / (NDVI_BOOST_PARK * PARKING_SQM)
            L += [
                "PARKING LOT CONVERSION ESTIMATES",
                "-" * 40,
                "  Reference unit: standard U.S. parking space (8.5 × 18 ft, ~14.2 m²)",
                "  Conversion type: asphalt → vegetated ground cover",
                "  (grass, bioswales, permeable pavers with plantings)",
                "",
                f"  Spaces to convert per acre:       ~{spa:.1f}",
                f"  Spaces to convert per sq mile:    ~{spmi:,.0f}",
                f"  Spaces to convert per 100 sq mi:  ~{spmi*100:,.0f}",
                "",
                "  Methodology: asphalt NDVI ~0.05 → vegetated surface NDVI ~0.40;",
                "  net NDVI gain of 0.35 per converted space.",
                "",
            ]

        if rpt_counties:
            s2 = sim.copy()
            s2["CKD_Reduction"] = s2["Predicted_CKD"] - s2["Simulated_CKD"]
            top10 = s2.nlargest(10, "CKD_Reduction")[
                ["State_Name", "COUNTY_FIPS", "Risk_Level",
                 "Predicted_CKD", "Simulated_CKD", "CKD_Reduction", "Population"]
            ]
            L += [
                "TOP 10 COUNTIES — GREATEST PROJECTED CKD REDUCTION",
                "-" * 40,
                f"  {'State':<20} {'FIPS':<7} {'Risk':<8} "
                f"{'Base%':>7} {'Sim%':>7} {'Delta':>8} {'Population':>12}",
                "  " + "-" * 72,
            ]
            for _, r in top10.iterrows():
                L.append(
                    f"  {r['State_Name']:<20} {r['COUNTY_FIPS']:<7} {r['Risk_Level']:<8}"
                    f" {r['Predicted_CKD']:>6.2f}%  {r['Simulated_CKD']:>6.2f}%"
                    f"  {r['CKD_Reduction']:>7.3f}  {int(r['Population']):>12,}"
                )
            L += [""]

        L += [
            "=" * 60,
            "DISCLAIMER",
            "-" * 40,
            "These projections are modeled estimates derived from observed",
            "2018–2020 county-level environmental and health data. Tree",
            "planting and parking conversion figures are approximations",
            "intended to illustrate policy scale. Consult primary literature",
            "and CITATIONS_NEEDED.md before use in formal policy documents.",
            "=" * 60,
        ]
        return "\n".join(L)

    st.download_button(
        label="Download Report (.txt)",
        data=_build_report(),
        file_name=f"ckd_scenario_gs{greenspace_pct}pct.txt",
        mime="text/plain",
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER — banner + nav
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="site-banner">
  <div class="banner-inner">
    <div>
      <div class="banner-title">CKD Green Space Policy Simulator</div>
      <div class="banner-sub">
        Environmental Determinants of Chronic Kidney Disease &nbsp;·&nbsp;
        U.S. County-Level Analysis
      </div>
    </div>
    <div class="banner-meta">
      CSE 6242 Visual Analytics<br>
      Georgia Tech &nbsp;·&nbsp; Team 059
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

page = option_menu(
    menu_title=None,
    options=["Green Space Simulator", "Multi-Factor Analysis", "County Explorer", "Glossary"],
    icons=["", "", "", ""],          # hide bootstrap icons — text-only nav
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0",
            "background-color": CDC_WHITE,
            "border-bottom": f"1px solid {CDC_BORDER}",
            "margin-bottom": "0",
        },
        "nav": {"padding": "0 8px"},
        "icon": {"display": "none"},
        "nav-link": {
            "font-size": "13.5px",
            "font-weight": "500",
            "color": CDC_TEXT,
            "padding": "13px 22px",
            "border-radius": "0",
            "border-bottom": "3px solid transparent",
            "--hover-color": "#eef3f8",
        },
        "nav-link-selected": {
            "background-color": "transparent",
            "color": CDC_NAVY,
            "font-weight": "700",
            "border-bottom": f"3px solid {CDC_BLUE}",
        },
    },
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: Green Space Simulator
# ══════════════════════════════════════════════════════════════════════════════
if page == "Green Space Simulator":

    st.info(
        "**How this works:** Adjust the Green Space slider in the left panel to simulate "
        "county-level investment in parks, tree canopy, and urban vegetation. The model "
        "uses pre-computed predictions at 0%, 10%, 20%, 50%, and 100% green space "
        "increases, interpolated to your selected value. Maps update in real time."
    )

    render_stats(sim)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    _section("Projected CKD Reduction by County")
    st.plotly_chart(build_delta_map(sim, geojson),
                    use_container_width=True, key="p1_delta_map")

    _section("Risk Level Comparison — Baseline vs. Simulated Intervention")
    map_l, map_r = st.columns(2)
    with map_l:
        st.plotly_chart(
            build_choropleth(sim, geojson, "Risk_Level", "Predicted_CKD",
                             "Future CKD Risk — Baseline (No Intervention)"),
            use_container_width=True, key="p1_map_baseline",
        )
    with map_r:
        st.plotly_chart(
            build_choropleth(sim, geojson, "Simulated_Risk", "Simulated_CKD",
                             f"Future CKD Risk — +{greenspace_pct}% Green Space"),
            use_container_width=True, key="p1_map_simulated",
        )

    with st.expander("Risk category shift detail"):
        before  = sim["Risk_Level"].value_counts().rename("Baseline")
        after   = sim["Simulated_Risk"].value_counts().rename("Simulated")
        compare = pd.concat([before, after], axis=1).reset_index()
        compare.columns = ["Risk", "Baseline", "Simulated"]
        fig_bar = px.bar(
            compare.melt(id_vars="Risk", var_name="Scenario", value_name="Counties"),
            x="Risk", y="Counties", color="Scenario", barmode="group",
            color_discrete_map={"Baseline": "#5a7fa8", "Simulated": CDC_GREEN},
            category_orders={"Risk": ["Low", "Medium", "High"]},
            title="Risk Category Distribution: Baseline vs. Simulated",
        )
        fig_bar.update_layout(paper_bgcolor=CDC_WHITE, plot_bgcolor=CDC_LIGHT)
        st.plotly_chart(fig_bar, use_container_width=True, key="p1_risk_bar")

    with st.expander("Top 15 counties with greatest projected CKD reduction"):
        sim["CKD_Reduction"] = sim["Predicted_CKD"] - sim["Simulated_CKD"]
        top15 = (
            sim.nlargest(15, "CKD_Reduction")
            [["State_Name", "COUNTY_FIPS", "Green_Space_Index", "Risk_Level",
              "Predicted_CKD", "Simulated_CKD", "CKD_Reduction", "Population"]]
            .rename(columns={
                "State_Name": "State", "COUNTY_FIPS": "County FIPS",
                "Green_Space_Index": "Green Space Index", "Risk_Level": "Baseline Risk",
                "Predicted_CKD": "Baseline CKD%", "Simulated_CKD": "Simulated CKD%",
                "CKD_Reduction": "Reduction (pp)",
            })
            .reset_index(drop=True)
        )
        st.dataframe(top15, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: Multi-Factor Analysis
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Multi-Factor Analysis":

    st.info(
        "Green space remains the primary policy lever. This page allows you to layer "
        "additional environmental and socioeconomic interventions to model combined "
        "scenarios. Secondary factor effect sizes are approximate and intended for "
        "exploratory use — see the Glossary for methodology notes."
    )

    _section("Policy Scenario Inputs")
    c1, c2 = st.columns(2)
    with c1:
        gs2      = st.slider("Green Space Increase (%)", 0, 100, 10, 1, key="gs2")
        pm25_pct = st.slider("PM2.5 Reduction (%)", 0, 50, 0, 5,
                             help="Reduction in fine particulate matter concentration.")
    with c2:
        traffic_pct = st.slider("Traffic Exposure Reduction (%)", 0, 50, 0, 5,
                                help="Reduction in road traffic proximity (PTRAF) exposure.")
        income_pct  = st.slider("Low-Income Population Reduction (%)", 0, 30, 0, 5,
                                help="Proxy for economic investment and poverty reduction programs.")

    sim2 = simulate_multifactor(county_gdf, gs2, pm25_pct, traffic_pct, income_pct)

    _section("Simulated Health Impact")
    render_stats(sim2)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    _section("Risk Level Comparison — Baseline vs. Multi-Factor Intervention")
    ml, mr = st.columns(2)
    with ml:
        st.plotly_chart(
            build_choropleth(sim2, geojson, "Risk_Level", "Predicted_CKD",
                             "Future CKD Risk — Baseline"),
            use_container_width=True, key="p2_map_baseline",
        )
    with mr:
        st.plotly_chart(
            build_choropleth(sim2, geojson, "Simulated_Risk", "Simulated_CKD",
                             "Future CKD Risk — Multi-Factor Intervention"),
            use_container_width=True, key="p2_map_simulated",
        )

    _section("Estimated CKD Reduction by Policy Factor")
    gs_only  = simulate_greenspace(county_gdf, gs2)["Simulated_CKD"].mean()
    baseline = county_gdf["Predicted_CKD"].mean()
    contributions = {
        "Green Space":     baseline - gs_only,
        "PM2.5 Reduction": pm25_pct   * 0.0025 * baseline,
        "Traffic":         traffic_pct * 0.0015 * baseline,
        "Income":          income_pct  * 0.003  * baseline,
    }
    contrib_df = pd.DataFrame({
        "Factor": list(contributions.keys()),
        "CKD Reduction (pp)": list(contributions.values()),
    })
    fig_contrib = px.bar(
        contrib_df, x="Factor", y="CKD Reduction (pp)", color="Factor",
        color_discrete_sequence=[CDC_GREEN, CDC_BLUE, "#7b5ea7", CDC_AMBER],
        title="Estimated CKD Reduction Attributable to Each Policy Factor",
    )
    fig_contrib.update_layout(paper_bgcolor=CDC_WHITE, plot_bgcolor=CDC_LIGHT,
                               showlegend=False)
    st.plotly_chart(fig_contrib, use_container_width=True, key="p2_contrib_bar")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: County Explorer
# ══════════════════════════════════════════════════════════════════════════════
elif page == "County Explorer":

    _section("Geographic Risk Explorer")
    states     = sorted(county_gdf["State_Name"].unique())
    sel_states = st.multiselect("Filter by State (leave blank to view all states)", states)
    view       = county_gdf if not sel_states else county_gdf[county_gdf["State_Name"].isin(sel_states)]

    if sel_states:
        st.plotly_chart(
            build_state_choropleth(view, "Risk_Level", "CKD_Prevalence",
                                   f"CKD Risk by County — {', '.join(sel_states)}"),
            use_container_width=True, key="p3_state_map",
        )
    else:
        st.plotly_chart(
            build_choropleth(county_gdf, county_gdf.__geo_interface__,
                             "Risk_Level", "CKD_Prevalence",
                             "CKD Risk by County — All States"),
            use_container_width=True, key="p3_state_map",
        )

    _section("Green Space Index vs. CKD Prevalence")
    fig_scatter = px.scatter(
        view,
        x="Green_Space_Index", y="CKD_Prevalence",
        color="Risk_Level", size="Population", size_max=30,
        color_discrete_map=RISK_COLORS,
        hover_data=["State_Name", "COUNTY_FIPS", "PM25", "LOWINCPCT"],
        trendline="ols",
        title="Green Space Index vs. CKD Prevalence (bubble size proportional to population)",
        labels={
            "Green_Space_Index": "Green Space Index (NDVI)",
            "CKD_Prevalence": "CKD Prevalence (%)",
            "Risk_Level": "Risk Level",
        },
    )
    fig_scatter.update_layout(paper_bgcolor=CDC_WHITE, plot_bgcolor=CDC_LIGHT)
    st.plotly_chart(fig_scatter, use_container_width=True, key="p3_scatter")

    with st.expander("View county-level data table"):
        display_cols = [
            "State_Name", "COUNTY_FIPS", "Risk_Level", "CKD_Prevalence",
            "Predicted_CKD", "Green_Space_Index", "PM25", "OZONE",
            "PTRAF", "LOWINCPCT", "Population",
        ]
        tab3_view = view[display_cols].reset_index(drop=True)
        st.dataframe(tab3_view, use_container_width=True)
        st.download_button(
            "Download filtered county data (CSV)",
            data=tab3_view.to_csv(index=False),
            file_name="ckd_county_explorer.csv",
            mime="text/csv",
            key="p3_csv_download",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: Glossary
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Glossary":

    st.markdown("## Reference Glossary")
    st.markdown(
        "Technical, environmental, and statistical terms used throughout this tool. "
        "Definitions are written for a policy and public health audience."
    )

    def term(name, definition, example=None):
        ex_html = (f'<div class="term-example">{example}</div>' if example else "")
        st.markdown(f"""
        <div class="term-name">{name}</div>
        <div class="term-def">{definition}</div>
        {ex_html}
        <hr class="term-divider">
        """, unsafe_allow_html=True)

    with st.expander("Health & Disease Terms", expanded=True):
        term("Chronic Kidney Disease (CKD)",
             "A long-term condition in which the kidneys gradually lose their capacity to filter "
             "waste and excess fluid from the blood. Staged 1–5 by severity. The leading causes "
             "are sustained hypertension and diabetes.",
             "A county CKD prevalence of 4.0% indicates approximately 4 in every 100 adults "
             "carry a diagnosis.")
        term("CKD Prevalence (%)",
             "The proportion of adults in a given geography with an active CKD diagnosis at a "
             "point in time. Distinct from incidence, which counts only new cases per year.")
        term("Hypertension",
             "Chronically elevated blood pressure (≥130/80 mmHg). Sustained hypertension "
             "damages the renal microvasculature over time and is the leading modifiable "
             "risk factor for CKD progression.")
        term("Predicted CKD (%)",
             "County-level CKD rate estimated by the Gradient Boosting Regressor from "
             "environmental and socioeconomic features. Represents a modeled projection, "
             "not a directly observed clinical measurement.")
        term("Risk Level (Low / Medium / High)",
             "County classification based on predicted CKD rate relative to the national "
             "distribution. Thresholds are data-derived percentiles, not clinical cut-offs. "
             "Risk level can only decrease under simulated green space interventions.")

    with st.expander("Green Space & Environmental Terms", expanded=True):
        term("NDVI — Normalized Difference Vegetation Index",
             "A satellite-derived index of vegetation density, computed from the ratio of "
             "near-infrared to red light reflectance. Healthy plant tissue strongly absorbs "
             "red and reflects near-infrared; impervious surfaces do the opposite. Range: 0 to 1.",
             "Asphalt: ~0.05 · Sparse urban lawn: ~0.20 · Dense urban park: ~0.50 · "
             "Temperate forest: ~0.80")
        term("Green Space Index",
             "The NDVI value assigned to each U.S. census tract in this dataset. The "
             "national county study average is 0.22, consistent with low-to-moderate "
             "urban vegetation density.")
        term("Impervious Surface",
             "Any engineered surface that prevents precipitation infiltration — pavement, "
             "rooftops, compacted gravel. Higher impervious cover correlates with lower NDVI, "
             "elevated urban heat island effect, and reduced air quality.")
        term("Tree Caliper",
             "Standard nursery specification for trunk diameter, measured 6 inches above "
             "ground grade (ANSI Z60.1). A proxy for tree size and establishment cost at "
             "time of planting.",
             '1–2" caliper: newly planted. 4–6" caliper: established street tree. '
             '8–12" caliper: large mature specimen.')
        term("Canopy Spread",
             "The horizontal extent of a tree's foliage projected onto the ground, as seen "
             "from above. The canopy is the primary driver of NDVI contribution in satellite "
             "imagery. Spread increases with age; estimates in this tool reflect mature canopy "
             "typically achieved 10–15 years after planting.")
        term("Bioswale",
             "A vegetated drainage channel engineered to slow, filter, and infiltrate "
             "stormwater runoff. Frequently used to convert impervious parking medians and "
             "curb strips into productive green infrastructure. Increases NDVI, mitigates "
             "urban heat, and reduces combined sewer overflows.")
        term("PM2.5 — Fine Particulate Matter",
             "Airborne particles with aerodynamic diameter ≤2.5 micrometers. Penetrates the "
             "pulmonary alveoli and enters systemic circulation. Associated with cardiovascular "
             "inflammation and accelerated CKD progression. Measured in μg/m³.",
             "EPA NAAQS annual standard: 9 μg/m³ (revised 2024). Study range: ~6–15 μg/m³.")
        term("Ozone (OZONE)",
             "Tropospheric ozone formed via photochemical reaction of NOₓ and VOCs from "
             "combustion sources. A criteria air pollutant linked to respiratory and "
             "cardiovascular morbidity. Reported in parts per billion (ppb).")
        term("PTRAF — Traffic Proximity Index",
             "EPA EJScreen indicator measuring residential proximity to major roadways, "
             "weighted by annual average daily traffic volume. Elevated values indicate "
             "greater exposure to vehicular exhaust, noise, and re-suspended road dust.")

    with st.expander("Data & Modeling Terms", expanded=True):
        term("Census Tract",
             "A small, statistically stable geographic subdivision defined by the U.S. Census "
             "Bureau, designed to contain 1,200–8,000 residents. The primary spatial unit of "
             "data collection in this study. Multiple tracts aggregate to each county.")
        term("GEOID",
             "The Census Bureau's 11-digit concatenated geographic identifier for a census "
             "tract: 2-digit state FIPS + 3-digit county FIPS + 6-digit tract code.",
             "13121010100 → Georgia (13) / Fulton County (121) / Tract 010100")
        term("County FIPS Code",
             "A 5-digit Federal Information Processing Standards numeric code uniquely "
             "identifying each U.S. county. First 2 digits: state. Next 3: county.",
             "13121 → Fulton County, Georgia")
        term("LOWINCPCT — Low-Income Percentage",
             "Share of census tract population with household income at or below 200% of "
             "the federal poverty level. Sourced from EPA EJScreen as a proxy for economic "
             "vulnerability and limited healthcare access.")
        term("Gradient Boosting Regressor",
             "An ensemble machine learning algorithm that constructs a prediction by "
             "sequentially fitting shallow decision trees, each minimizing the residual "
             "error of its predecessor. Well-suited to tabular data with heterogeneous "
             "feature types and non-linear relationships.")
        term("R² (Coefficient of Determination)",
             "Proportion of variance in observed CKD rates explained by the model's "
             "predictions. Ranges 0–1; higher is better. This model achieves R² = 0.44, "
             "indicating that 44% of county-level CKD variability is captured by the "
             "environmental and socioeconomic features included.")
        term("Percent Age 65+",
             "Share of county population aged 65 or older. Included as a model covariate "
             "because CKD prevalence increases substantially with age, independent of "
             "environmental exposure.")
        term("Percent Uninsured",
             "Share of county population without health insurance coverage. Associated with "
             "delayed diagnosis and reduced treatment access, contributing to higher measured "
             "CKD prevalence in affected communities.")
