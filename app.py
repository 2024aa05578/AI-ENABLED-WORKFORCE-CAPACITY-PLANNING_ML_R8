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

DEFAULT_GROWTH_PARAMETERS = {
    "North": {
        "UPS": {"BAU": 20.0, "DC": 10.0},
        "Cooling": {"BAU": 20.0, "DC": 10.0},
        "Power Products": {"BAU": 15.0, "DC": 5.0},
        "Power System": {"BAU": 15.0, "DC": 5.0},
        "Industrial Automation": {"BAU": 15.0, "DC": 5.0},
    },
    "West": {
        "UPS": {"BAU": 30.0, "DC": 20.0},
        "Cooling": {"BAU": 30.0, "DC": 20.0},
        "Power Products": {"BAU": 20.0, "DC": 10.0},
        "Power System": {"BAU": 20.0, "DC": 10.0},
        "Industrial Automation": {"BAU": 20.0, "DC": 10.0},
    },
    "South": {
        "UPS": {"BAU": 22.0, "DC": 10.0},
        "Cooling": {"BAU": 22.0, "DC": 10.0},
        "Power Products": {"BAU": 20.0, "DC": 5.0},
        "Power System": {"BAU": 20.0, "DC": 5.0},
        "Industrial Automation": {"BAU": 20.0, "DC": 5.0},
    },
    "East": {
        "UPS": {"BAU": 15.0, "DC": 5.0},
        "Cooling": {"BAU": 15.0, "DC": 5.0},
        "Power Products": {"BAU": 15.0, "DC": 5.0},
        "Power System": {"BAU": 15.0, "DC": 5.0},
        "Industrial Automation": {"BAU": 15.0, "DC": 5.0},
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

APP_SCHEMA_VERSION = "v20_three_year_h1h2_ml_feedback"


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
        rows.append(
            {
                "Product": PRODUCT_DISPLAY[product],
                "BAU": float(growth_parameters[region][product]["BAU"]),
                "DC": float(growth_parameters[region][product]["DC"]),
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
                    "DC": float(row["DC"]),
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

    unnamed_columns = [
        column for column in df.columns
        if str(column).startswith("Unnamed")
    ]

    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    return df


def validate_input_data(df):
    required_columns = [
        "Region",
        "Product",
        "Current_SE",
        "Breakdown_WO",
        "Breakdown_Hrs",
        "PM_WO",
        "PM_Hrs",
        "Startup_WO",
        "Startup_Hrs",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    df = df.copy()

    df["Region"] = df["Region"].astype(str).str.strip()
    df["Product"] = df["Product"].astype(str).str.strip().replace(PRODUCT_ALIASES)

    invalid_regions = sorted(set(df["Region"].unique()) - set(REGIONS))
    invalid_products = sorted(set(df["Product"].unique()) - set(PRODUCTS))

    if invalid_regions:
        st.error(f"Invalid regions found: {invalid_regions}")
        st.stop()

    if invalid_products:
        st.error(f"Invalid products found: {invalid_products}")
        st.stop()

    numeric_columns = [
        "Current_SE",
        "Breakdown_WO",
        "Breakdown_Hrs",
        "PM_WO",
        "PM_Hrs",
        "Startup_WO",
        "Startup_Hrs",
    ]

    if "Year" in df.columns:
        numeric_columns.append("Year")

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[numeric_columns].isnull().any().any():
        st.error("Some numeric columns contain blank or invalid numeric values.")
        st.stop()

    return df


def show_bar_chart_with_values(data, x_col, y_col, title, color_col=None):
    if color_col is None:
        color_col = x_col

    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        text=y_col,
        title=title,
        color_discrete_sequence=[
            "#1F77B4",
            "#FF7F0E",
            "#2CA02C",
            "#D62728",
            "#9467BD",
            "#8C564B",
            "#E377C2",
            "#7F7F7F",
            "#BCBD22",
            "#17BECF",
        ],
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=430,
        title_x=0.05,
        showlegend=False,
        margin=dict(l=40, r=30, t=70, b=90),
        xaxis_title="",
        yaxis_title="Engineers",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#243447"),
    )

    fig.update_xaxes(
        fixedrange=True,
        tickangle=-20,
    )

    fig.update_yaxes(
        fixedrange=True,
        rangemode="tozero",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": False,
            "staticPlot": False,
        },
    )


def apply_feedback_correction(result, feedback_df):
    adjusted = result.copy()
    adjusted["ML Correction Factor"] = 1.0
    adjusted["ML Adjusted Required SE"] = adjusted["Combined Required Engineers"]

    if feedback_df is None or feedback_df.empty:
        return adjusted, pd.DataFrame()

    feedback_df = feedback_df.copy()

    required_columns = [
        "Forecast Year",
        "Region",
        "Product",
        "System Forecast SE",
        "Manual Forecast SE",
    ]

    if any(column not in feedback_df.columns for column in required_columns):
        return adjusted, pd.DataFrame()

    for column in [
        "Forecast Year",
        "System Forecast SE",
        "Manual Forecast SE",
    ]:
        feedback_df[column] = pd.to_numeric(
            feedback_df[column],
            errors="coerce",
        )

    feedback_df = feedback_df.dropna(
        subset=[
            "Forecast Year",
            "Region",
            "Product",
            "System Forecast SE",
            "Manual Forecast SE",
        ]
    )

    feedback_df = feedback_df[
        feedback_df["System Forecast SE"] > 0
    ]

    if feedback_df.empty:
        return adjusted, pd.DataFrame()

    feedback_df["Correction Factor"] = (
        feedback_df["Manual Forecast SE"]
        / feedback_df["System Forecast SE"]
    )

    factors = (
        feedback_df.groupby(["Region", "Product"])["Correction Factor"]
        .mean()
        .reset_index()
    )

    adjusted = adjusted.merge(
        factors,
        on=["Region", "Product"],
        how="left",
    )

    adjusted["Correction Factor"] = adjusted["Correction Factor"].fillna(1.0)

    adjusted["ML Correction Factor"] = adjusted["Correction Factor"].round(3)

    adjusted["ML Adjusted Required SE"] = (
        adjusted["Combined Required Engineers"]
        * adjusted["Correction Factor"]
    ).round(1)

    adjusted = adjusted.drop(columns=["Correction Factor"])

    return adjusted, factors


def build_feedback_template(result):
    return (
        result[
            [
                "Forecast Year",
                "Region",
                "Product",
                "Combined Required Engineers",
            ]
        ]
        .rename(
            columns={
                "Combined Required Engineers": "System Forecast SE"
            }
        )
        .assign(
            **{
                "Manual Forecast SE": "",
                "Remarks": "",
            }
        )
    )


# =====================================================
# INITIALIZE STATE
# =====================================================

init_state()


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Planning Assumptions")

st.sidebar.markdown(
    """
    <div class="sidebar-note">
        Edit assumptions and click Apply. Dashboard refreshes only after applying.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar.form("planning_assumptions_form"):
    st.subheader("Region and Product Wise Growth")

    edited_growth_dfs = {}

    for region in REGIONS:
        show_region_header(region)

        edited_growth_dfs[region] = st.data_editor(
            growth_region_to_df(
                st.session_state.growth_parameters,
                region,
            ),
            hide_index=True,
            use_container_width=True,
            disabled=["Product"],
            height=205,
            column_config={
                "Product": st.column_config.TextColumn(
                    "Product",
                    width=112,
                ),
                "BAU": st.column_config.NumberColumn(
                    BAU_UP_LABEL,
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=54,
                ),
                "DC": st.column_config.NumberColumn(
                    DC_UP_LABEL,
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=54,
                ),
            },
            key=f"growth_data_editor_{region.lower()}",
        )

    st.subheader("BU Wise Attrition")

    edited_attrition_df = st.data_editor(
        attrition_dict_to_df(
            st.session_state.attrition_parameters
        ),
        hide_index=True,
        use_container_width=True,
        disabled=["Product"],
        height=210,
        column_config={
            "Product": st.column_config.TextColumn(
                "Product",
                width=118,
            ),
            "Attr %": st.column_config.NumberColumn(
                "Attr %",
                min_value=0.0,
                max_value=30.0,
                step=0.5,
                width=58,
            ),
        },
        key="attrition_data_editor",
    )

    st.subheader("Workforce Productivity")

    edited_productivity_df = st.data_editor(
        productivity_to_df(),
        hide_index=True,
        use_container_width=True,
        height=85,
        column_config={
            "Hrs/Day": st.column_config.NumberColumn(
                "Hrs/Day",
                min_value=1.0,
                max_value=24.0,
                step=0.5,
                width=64,
            ),
            "Days/M": st.column_config.NumberColumn(
                "Days/M",
                min_value=1,
                max_value=31,
                step=1,
                width=58,
            ),
            "Util %": st.column_config.NumberColumn(
                "Util %",
                min_value=1.0,
                max_value=100.0,
                step=1.0,
                width=58,
            ),
        },
        key="productivity_data_editor",
    )

    st.subheader("Hiring Split")

    edited_hiring_split_df = st.data_editor(
        hiring_split_to_df(
            st.session_state.hiring_split_parameters
        ),
        hide_index=True,
        use_container_width=True,
        disabled=["Forecast Year"],
        height=130,
        column_config={
            "Forecast Year": st.column_config.NumberColumn(
                "Year",
                width=70,
            ),
            "H1 %": st.column_config.NumberColumn(
                "H1 %",
                min_value=0.0,
                max_value=100.0,
                step=5.0,
                width=55,
            ),
            "H2 %": st.column_config.NumberColumn(
                "H2 %",
                min_value=0.0,
                max_value=100.0,
                step=5.0,
                width=55,
            ),
        },
        key="hiring_split_editor",
    )

    apply_assumptions = st.form_submit_button("Apply Assumptions")


if apply_assumptions:
    st.session_state.growth_parameters = growth_region_dfs_to_dict(
        edited_growth_dfs
    )

    st.session_state.attrition_parameters = attrition_df_to_dict(
        edited_attrition_df
    )

    st.session_state.hiring_split_parameters = hiring_split_df_to_dict(
        edited_hiring_split_df
    )

    (
        st.session_state.productive_hours,
        st.session_state.working_days,
        st.session_state.target_utilization,
    ) = productivity_df_to_values(
        edited_productivity_df
    )

    st.session_state.needs_recalc = True
    st.sidebar.success("Assumptions applied. Dashboard will refresh.")


# =====================================================
