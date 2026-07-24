import copy
import math
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

from workforce_model import calculate_workforce


st.set_page_config(
    page_title="AI Enabled Workforce & Capacity Planning",
    page_icon="🚀",
    layout="wide",
)


UP_ARROW = chr(8593)
BAU_UP_LABEL = "BAU " + UP_ARROW + "%"
DC_UP_LABEL = "DC " + UP_ARROW + "%"
FORECAST_YEARS = [2027, 2028, 2029]


# =====================================================
# COMPACT FIXED SIDEBAR WITH COLORS
# =====================================================

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        width: 380px !important;
        min-width: 380px !important;
        max-width: 380px !important;
        background: linear-gradient(180deg,#F8FAFC 0%,#EEF4FA 100%);
    }

    section[data-testid="stSidebar"] > div {
        width: 380px !important;
        min-width: 380px !important;
        max-width: 380px !important;
        padding-left: 6px !important;
        padding-right: 6px !important;
    }

    div[data-testid="stSidebarContent"] {
        width: 380px !important;
        max-width: 380px !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 12px !important;
        margin-top: 5px !important;
        margin-bottom: 3px !important;
        color: #1F4E79 !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        font-size: 9px !important;
        line-height: 1.1 !important;
    }

    section[data-testid="stSidebar"] button {
        font-size: 10px !important;
        padding-top: 3px !important;
        padding-bottom: 3px !important;
        background-color: #1F4E79 !important;
        color: white !important;
        border-radius: 6px !important;
    }

    .region-header {
        padding: 5px 8px;
        border-radius: 7px;
        margin-top: 6px;
        margin-bottom: 4px;
        font-weight: 700;
        font-size: 11px;
    }

    .sidebar-note {
        font-size: 9px;
        color: #475569;
        padding: 5px 7px;
        border-radius: 6px;
        background: #EAF2F8;
        border-left: 3px solid #1F4E79;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# MASTER DATA
# =====================================================

REGIONS = ["North", "West", "South", "East"]

PRODUCTS = [
    "UPS",
    "Cooling",
    "Power Products",
    "Power System",
    "Industrial Automation",
]

PRODUCT_ALIASES = {
    "Power Product": "Power Products",
    "Power Products": "Power Products",
    "Power System": "Power System",
    "Industrial Automation": "Industrial Automation",
    "Industiral Automation": "Industrial Automation",
    "UPS": "UPS",
    "Cooling": "Cooling",
}

PRODUCT_DISPLAY = {
    "UPS": "UPS",
    "Cooling": "Cooling",
    "Power Products": "Power Prod",
    "Power System": "Power Sys",
    "Industrial Automation": "Ind Auto",
}

PRODUCT_REVERSE_DISPLAY = {
    value: key for key, value in PRODUCT_DISPLAY.items()
}

REGION_STYLES = {
    "North": {
        "bg": "#EAF4FF",
        "border": "#1F77B4",
        "text": "#174A7C",
    },
    "West": {
        "bg": "#FFF4E5",
        "border": "#FF7F0E",
        "text": "#8A4A00",
    },
    "South": {
        "bg": "#EAF8EF",
        "border": "#2CA02C",
        "text": "#1B6B28",
    },
    "East": {
        "bg": "#F3EAFB",
        "border": "#9467BD",
        "text": "#573B78",
    },
}


# =====================================================
# DEFAULT PARAMETERS
# =====================================================

def make_growth(bau, dc_2027, dc_2028, dc_2029):
    return {
        "BAU": float(bau),
        "DC": {
            2027: float(dc_2027),
            2028: float(dc_2028),
            2029: float(dc_2029),
        },
    }


DEFAULT_GROWTH_PARAMETERS = {
    "North": {
        "UPS": make_growth(20.0, 10.0, 8.0, 6.0),
        "Cooling": make_growth(20.0, 10.0, 9.0, 7.0),
        "Power Products": make_growth(15.0, 5.0, 5.0, 5.0),
        "Power System": make_growth(15.0, 5.0, 6.0, 7.0),
        "Industrial Automation": make_growth(15.0, 5.0, 5.0, 6.0),
    },
    "West": {
        "UPS": make_growth(30.0, 20.0, 15.0, 10.0),
        "Cooling": make_growth(30.0, 20.0, 15.0, 10.0),
        "Power Products": make_growth(20.0, 10.0, 9.0, 8.0),
        "Power System": make_growth(20.0, 10.0, 9.0, 8.0),
        "Industrial Automation": make_growth(20.0, 10.0, 8.0, 7.0),
    },
    "South": {
        "UPS": make_growth(22.0, 10.0, 8.0, 6.0),
        "Cooling": make_growth(22.0, 10.0, 9.0, 7.0),
        "Power Products": make_growth(20.0, 5.0, 6.0, 7.0),
        "Power System": make_growth(20.0, 5.0, 6.0, 7.0),
        "Industrial Automation": make_growth(20.0, 5.0, 5.0, 6.0),
    },
    "East": {
        "UPS": make_growth(15.0, 5.0, 5.0, 5.0),
        "Cooling": make_growth(15.0, 5.0, 5.0, 5.0),
        "Power Products": make_growth(15.0, 5.0, 5.0, 5.0),
        "Power System": make_growth(15.0, 5.0, 5.0, 5.0),
        "Industrial Automation": make_growth(15.0, 5.0, 5.0, 5.0),
    },
}

DEFAULT_ATTRITION = {
    "UPS": 8.0,
    "Cooling": 8.0,
    "Power Products": 8.0,
    "Power System": 8.0,
    "Industrial Automation": 8.0,
}

DEFAULT_HIRING_SPLIT = {
    2027: {"H1": 60.0, "H2": 40.0},
    2028: {"H1": 50.0, "H2": 50.0},
    2029: {"H1": 50.0, "H2": 50.0},
}

APP_SCHEMA_VERSION = "v21_variable_dc_yearwise"


# =====================================================
# SESSION STATE
# =====================================================

def init_state():
    if st.session_state.get("schema_version") != APP_SCHEMA_VERSION:
        st.session_state.schema_version = APP_SCHEMA_VERSION
        st.session_state.growth_parameters = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)
        st.session_state.attrition_parameters = copy.deepcopy(DEFAULT_ATTRITION)
        st.session_state.hiring_split_parameters = copy.deepcopy(DEFAULT_HIRING_SPLIT)
        st.session_state.productive_hours = 7.0
        st.session_state.working_days = 20
        st.session_state.target_utilization = 90.0
        st.session_state.input_df = None
        st.session_state.result_df = None
        st.session_state.needs_recalc = False
        st.session_state.uploaded_file_id = None
        st.session_state.last_filter_signature = None


def show_region_header(region):
    style = REGION_STYLES[region]

    st.markdown(
        f"""
        <div class="region-header"
             style="background:{style['bg']};
                    border-left:4px solid {style['border']};
                    color:{style['text']};">
            {region} Growth
        </div>
        """,
        unsafe_allow_html=True,
    )


def growth_region_to_df(growth_parameters, region):
    rows = []

    for product in PRODUCTS:
        params = growth_parameters[region][product]
        dc_values = params.get("DC", {})

        if not isinstance(dc_values, dict):
            dc_values = {
                year: float(dc_values)
                for year in FORECAST_YEARS
            }

        rows.append(
            {
                "Product": PRODUCT_DISPLAY[product],
                "BAU": float(params.get("BAU", 0.0)),
                "DC 2027": float(dc_values.get(2027, dc_values.get("2027", 0.0))),
                "DC 2028": float(dc_values.get(2028, dc_values.get("2028", 0.0))),
                "DC 2029": float(dc_values.get(2029, dc_values.get("2029", 0.0))),
            }
        )

    return pd.DataFrame(rows)


def growth_region_dfs_to_dict(edited_growth_dfs):
    output = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)

    for region, growth_df in edited_growth_dfs.items():
        for _, row in growth_df.iterrows():
            product = PRODUCT_REVERSE_DISPLAY.get(str(row["Product"]).strip())

            if product in PRODUCTS:
                output[region][product] = {
                    "BAU": float(row["BAU"]),
                    "DC": {
                        2027: float(row["DC 2027"]),
                        2028: float(row["DC 2028"]),
                        2029: float(row["DC 2029"]),
                    },
                }

    return output


def attrition_dict_to_df(attrition_parameters):
    rows = []

    for product in PRODUCTS:
        rows.append(
            {
                "Product": PRODUCT_DISPLAY[product],
                "Attr %": float(attrition_parameters.get(product, 8.0)),
            }
        )

    return pd.DataFrame(rows)


def attrition_df_to_dict(attrition_df):
    output = copy.deepcopy(DEFAULT_ATTRITION)

    for _, row in attrition_df.iterrows():
        product = PRODUCT_REVERSE_DISPLAY.get(str(row["Product"]).strip())

        if product in PRODUCTS:
            output[product] = float(row["Attr %"])

    return output


def productivity_to_df():
    return pd.DataFrame(
        [
            {
                "Hrs/Day": float(st.session_state.productive_hours),
                "Days/M": int(st.session_state.working_days),
                "Util %": float(st.session_state.target_utilization),
            }
        ]
    )


def productivity_df_to_values(productivity_df):
    row = productivity_df.iloc[0]

    return (
        float(row["Hrs/Day"]),
        int(row["Days/M"]),
        float(row["Util %"]),
    )


def hiring_split_to_df(split_parameters):
    rows = []

    for year in FORECAST_YEARS:
        rows.append(
            {
                "Forecast Year": year,
                "H1 %": float(split_parameters[year]["H1"]),
                "H2 %": float(split_parameters[year]["H2"]),
            }
        )

    return pd.DataFrame(rows)


def hiring_split_df_to_dict(split_df):
    output = copy.deepcopy(DEFAULT_HIRING_SPLIT)

    for _, row in split_df.iterrows():
        year = int(row["Forecast Year"])
        h1 = float(row["H1 %"])
        h2 = float(row["H2 %"])

        total = h1 + h2

        if total <= 0:
            h1 = 50.0
            h2 = 50.0

        elif abs(total - 100.0) > 0.01:
            h1 = h1 * 100.0 / total
            h2 = h2 * 100.0 / total

        output[year] = {
            "H1": h1,
            "H2": h2,
        }

    return output


def safe_read_csv(uploaded_file):
    raw_bytes = uploaded_file.getvalue()

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin1")

    cleaned_lines = []

    for line in text.splitlines():
        line = line.strip()

        while line.endswith(","):
            line = line[:-1]

        cleaned_lines.append(line)

    df = pd.read_csv(
        StringIO("\n".join(cleaned_lines)),
        engine="python",
    )

    df.columns = df.columns.str.strip()

    unnamed_
