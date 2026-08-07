# ============================================================
# Forecast Model Version: v17_headcount_based_forecast
# Revised Full Replacement App
#
# Changes:
# - Removed VP wording
# - Kept Leadership View only
# - Leadership Readout converted to bullet points
# - Colorful left planning pane
# - Colorful leadership callout
# - Full workforce model included
# ============================================================

import streamlit as st
import pandas as pd
from io import BytesIO


# ============================================================
# Streamlit Page Config
# ============================================================

st.set_page_config(
    page_title="SE Workforce Forecast - Leadership View",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Global Styling
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background-color: #ffffff;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f2f6ff 0%, #eefaf3 52%, #fff8ec 100%);
            border-right: 1px solid #d8e1ef;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {
            color: #263142;
        }

        .left-pane-heading {
            font-size: 19px;
            font-weight: 800;
            color: #222b45;
            margin-bottom: 4px;
        }

        .left-pane-caption {
            font-size: 13px;
            color: #5d6678;
            margin-bottom: 16px;
        }

        .region-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 13px 14px;
            margin-top: 16px;
            margin-bottom: 10px;
            box-shadow: 0 3px 14px rgba(33, 48, 90, 0.08);
            border: 1px solid #e3e9f5;
        }

        .region-card-north {
            border-left: 7px solid #4f7cff;
        }

        .region-card-west {
            border-left: 7px solid #ff9f43;
        }

        .region-card-south {
            border-left: 7px solid #20c997;
        }

        .region-card-east {
            border-left: 7px solid #a066ff;
        }

        .region-card-title {
            font-size: 15px;
            font-weight: 800;
            color: #252a34;
            margin-bottom: 3px;
        }

        .region-card-subtitle {
            font-size: 12px;
            color: #697386;
        }

        div.stButton > button {
            background: linear-gradient(90deg, #4f7cff 0%, #20c997 100%);
            color: white;
            border: none;
            border-radius: 11px;
            font-weight: 800;
            padding: 0.58rem 1rem;
            width: 100%;
        }

        div.stButton > button:hover {
            background: linear-gradient(90deg, #3d66d6 0%, #17a884 100%);
            color: white;
            border: none;
        }

        .app-title {
            font-size: 31px;
            font-weight: 850;
            color: #252a34;
            margin-bottom: 6px;
        }

        .app-subtitle {
            font-size: 14px;
            color: #687386;
            margin-bottom: 22px;
        }

        .section-header {
            font-size: 23px;
            font-weight: 850;
            color: #2c3140;
            margin-top: 24px;
            margin-bottom: 12px;
        }

        .kpi-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-top: 12px;
            margin-bottom: 28px;
        }

        .kpi-card {
            background: #ffffff;
            border-radius: 17px;
            padding: 21px 23px;
            box-shadow: 0 5px 20px rgba(30, 45, 90, 0.09);
            border: 1px solid #edf0f7;
        }

        .kpi-card-blue {
            border-top: 7px solid #4f7cff;
            background: linear-gradient(180deg, #f5f8ff 0%, #ffffff 100%);
        }

        .kpi-card-purple {
            border-top: 7px solid #8e5cff;
            background: linear-gradient(180deg, #faf7ff 0%, #ffffff 100%);
        }

        .kpi-card-orange {
            border-top: 7px solid #ff9f43;
            background: linear-gradient(180deg, #fff8ef 0%, #ffffff 100%);
        }

        .kpi-label {
            font-size: 13px;
            color: #687386;
            font-weight: 700;
            margin-bottom: 9px;
        }

        .kpi-value {
            font-size: 36px;
            color: #242936;
            font-weight: 850;
            line-height: 1.05;
        }

        .leadership-callout {
            background: linear-gradient(135deg, #eef4ff 0%, #f8f0ff 45%, #fff8ec 100%);
            border: 1px solid #dfe7ff;
            border-left: 9px solid #4f7cff;
            border-radius: 20px;
            padding: 23px 28px;
            margin: 16px 0 28px 0;
            box-shadow: 0 6px 24px rgba(41, 65, 120, 0.10);
        }

        .leadership-callout-title {
            font-size: 24px;
            font-weight: 850;
            color: #242936;
            margin-bottom: 13px;
        }

        .leadership-callout ul {
            margin-top: 8px;
            margin-bottom: 0;
            padding-left: 23px;
        }

        .leadership-callout li {
            margin-bottom: 10px;
            font-size: 15px;
            color: #303747;
            line-height: 1.58;
        }

        .leadership-highlight {
            font-weight: 850;
            color: #1f5eff;
        }

        .leadership-warning {
            font-weight: 850;
            color: #d97706;
        }

        .leadership-success {
            font-weight: 850;
            color: #0f9f6e;
        }

        .metric-strip {
            background: #f7f9fc;
            border: 1px solid #e7ecf5;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 18px;
            color: #3c4658;
            font-size: 14px;
        }

        button[data-baseweb="tab"] {
            font-size: 14px;
            font-weight: 650;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ff4b4b;
        }

        div[data-testid="stDataFrame"] {
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Base Configuration
# ============================================================

BASE_YEAR = 2026
FORECAST_YEARS = [2027, 2028, 2029]

REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Prod", "Power Sys"]

PRODUCT_DISPLAY_MAP = {
    "UPS": "UPS",
    "Cooling": "Cooling",
    "Power Prod": "Power Product",
    "Power Sys": "Power System",
}

DEFAULT_BASE_SE = pd.DataFrame(
    [
        ["North", "UPS", 35],
        ["North", "Cooling", 18],
        ["North", "Power Prod", 12],
        ["North", "Power Sys", 16],
        ["West", "UPS", 47],
        ["West", "Cooling", 21],
        ["West", "Power Prod", 14],
        ["West", "Power Sys", 20],
        ["South", "UPS", 42],
        ["South", "Cooling", 20],
        ["South", "Power Prod", 13],
        ["South", "Power Sys", 19],
        ["East", "UPS", 22],
        ["East", "Cooling", 10],
        ["East", "Power Prod", 5],
        ["East", "Power Sys", 7],
    ],
    columns=["Region", "Product", "Current SE"],
)

DEFAULT_ATTRITION = {
    2027: 5.0,
    2028: 5.0,
    2029: 5.0,
}

DEFAULT_BAU_GROWTH = {
    "North": {"UPS": 10, "Cooling": 10, "Power Prod": 10, "Power Sys": 10},
    "West": {"UPS": 10, "Cooling": 10, "Power Prod": 10, "Power Sys": 10},
    "South": {"UPS": 10, "Cooling": 10, "Power Prod": 10, "Power Sys": 10},
    "East": {"UPS": 10, "Cooling": 10, "Power Prod": 10, "Power Sys": 10},
}

DEFAULT_DC_GROWTH = {
    "North": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
    "West": {"UPS": 4, "Cooling": 4, "Power Prod": 2, "Power Sys": 2},
    "South": {"UPS": 2, "Cooling": 2, "Power Prod": 0, "Power Sys": 0},
    "East": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
}


# ============================================================
# Utility Functions
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(round(float(value)))
    except Exception:
        return default


def pct_to_multiplier(pct_value):
    return 1 + safe_float(pct_value, 0) / 100


def render_region_card(region_name, css_class):
    st.markdown(
        f"""
        <div class="region-card {css_class}">
            <div class="region-card-title">{region_name} Growth</div>
            <div class="region-card-subtitle">Product-wise BAU and DC growth assumptions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_growth_editor_df(region):
    rows = []
    for product in PRODUCTS:
        rows.append(
            {
                "Product": product,
                "BAU ^%": DEFAULT_BAU_GROWTH[region][product],
                "DC ^%": DEFAULT_DC_GROWTH[region][product],
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_excel_bytes(sheets_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return output.getvalue()


# ============================================================
# Workforce Forecast Model
# ============================================================

class WorkforceForecastModel:
    def __init__(self, base_df, growth_inputs, attrition_inputs, selected_years):
        self.base_df = base_df.copy()
        self.growth_inputs = growth_inputs
        self.attrition_inputs = attrition_inputs
        self.selected_years = selected_years

    def run(self):
        detailed_rows = []

        for _, row in self.base_df.iterrows():
            region = row["Region"]
            product = row["Product"]
            current_se = safe_float(row["Current SE"], 0)

            previous_required_se = current_se
            previous_available_se = current_se

            for year in FORECAST_YEARS:
                region_growth_df = self.growth_inputs[region]
                product_growth_row = region_growth_df[region_growth_df["Product"] == product]

                if product_growth_row.empty:
                    bau_growth_pct = 0
                    dc_growth_pct = 0
                else:
                    bau_growth_pct = safe_float(product_growth_row["BAU ^%"].iloc[0], 0)
                    dc_growth_pct = safe_float(product_growth_row["DC ^%"].iloc[0], 0)

                attrition_pct = safe_float(self.attrition_inputs.get(year, 0), 0)

                available_after_attrition = previous_available_se * (1 - attrition_pct / 100)
                bau_required_se = previous_required_se * pct_to_multiplier(bau_growth_pct)
                dc_incremental_se = previous_required_se * (dc_growth_pct / 100)
                combined_required_se = bau_required_se + dc_incremental_se
                hiring_need = max(combined_required_se - available_after_attrition, 0)
                closing_available_se = available_after_attrition + hiring_need

                detailed_rows.append(
                    {
                        "Year": year,
                        "Region": region,
                        "Product": product,
                        "Product Display": PRODUCT_DISPLAY_MAP.get(product, product),
                        "Opening SE Base": round(previous_available_se, 2),
                        "Attrition %": attrition_pct,
                        "Available SE After Attrition": round(available_after_attrition, 2
