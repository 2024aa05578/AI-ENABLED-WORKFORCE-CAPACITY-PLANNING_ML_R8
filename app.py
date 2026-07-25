import copy
import math
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

from workforce_model import calculate_workforce, MODEL_VERSION

st.set_page_config(
    page_title="AI Enabled Workforce & Capacity Planning",
    page_icon="🚀",
    layout="wide",
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

FORECAST_YEARS = [2027, 2028, 2029]

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

DEFAULT_GROWTH_FACTORS = {
    region: {
        "2028 BAU Factor": 1.0,
        "2028 DC Factor": 1.0,
        "2029 BAU Factor": 1.0,
        "2029 DC Factor": 1.0,
    }
    for region in REGIONS
}

DEFAULT_ATTRITION = {
    product: 8.0 for product in PRODUCTS
}

APP_SCHEMA_VERSION = "v20_functional_inputs_exec_summary"


# =====================================================
# SESSION INITIALIZATION
# =====================================================
def init_state():
    if st.session_state.get("schema_version") != APP_SCHEMA_VERSION:
        st.session_state.schema_version = APP_SCHEMA_VERSION
        st.session_state.growth_parameters = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)
        st.session_state.growth_factors = copy.deepcopy(DEFAULT_GROWTH_FACTORS)
        st.session_state.attrition_parameters = copy.deepcopy(DEFAULT_ATTRITION)

        st.session_state.productive_hours = 7.0
        st.session_state.working_days = 20
        st.session_state.target_utilization = 90.0

        st.session_state.input_df = None
        st.session_state.result_df = None
        st.session_state.needs_recalc = False
        st.session_state.uploaded_file_id = None
        st.session_state.last_filter_signature = None


# =====================================================
# SIDEBAR HELPERS
# =====================================================
def growth_region_to_df(region):
    rows = []

    for product in PRODUCTS:
        params = st.session_state.growth_parameters[region][product]

        rows.append(
            {
                "Product": PRODUCT_DISPLAY[product],
                "BAU": float(params["BAU"]),
                "DC": float(params["DC"]),
            }
        )

    return pd.DataFrame(rows)


def growth_region_dfs_to_dict(edited_growth_dfs):
    values = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)

    for region, growth_df in edited_growth_dfs.items():
        for _, row in growth_df.iterrows():
            product_label = str(row["Product"]).strip()
            product = PRODUCT_REVERSE_DISPLAY.get(product_label)

            if product in PRODUCTS:
                values[region][product] = {
                    "BAU": float(row["BAU"]),
                    "DC": float(row["DC"]),
                }

    return values


def growth_factors_to_df():
    rows = []

    for region in REGIONS:
        row = {"Region": region}
        row.update(
            st.session_state.growth_factors.get(
                region,
                DEFAULT_GROWTH_FACTORS[region],
            )
        )
        rows.append(row)

    return pd.DataFrame(rows)


def growth_factors_df_to_dict(factor_df):
    values = copy.deepcopy(DEFAULT_GROWTH_FACTORS)

    for _, row in factor_df.iterrows():
        region = str(row["Region"]).strip()

        if region in REGIONS:
            values[region] = {
                "2028 BAU Factor": float(row["2028 BAU Factor"]),
                "2028 DC Factor": float(row["2028 DC Factor"]),
                "2029 BAU Factor": float(row["2029 BAU Factor"]),
                "2029 DC Factor": float(row["2029 DC Factor"]),
            }

    return values


def attrition_to_df():
    rows = []

    for product in PRODUCTS:
        rows.append(
            {
                "Product": PRODUCT_DISPLAY[product],
                "Attr %": float(st.session_state.attrition_parameters[product]),
            }
        )

    return pd.DataFrame(rows)


def attrition_df_to_dict(attrition_df):
    values = copy.deepcopy(DEFAULT_ATTRITION)

    for _, row in attrition_df.iterrows():
        product_label = str(row["Product"]).strip()
        product = PRODUCT_REVERSE_DISPLAY.get(product_label)

        if product in PRODUCTS:
            values[product] = float(row["Attr %"])

    return values


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


# =====================================================
# GENERAL HELPERS
# =====================================================
def add_total_row_and_column(matrix):
    matrix = matrix.copy()
    matrix["Total"] = matrix.sum(axis=1)

    total_row = pd.DataFrame(matrix.sum(axis=0)).T
    total_row.index = ["Total"]

    return pd.concat([matrix, total_row])


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

    cleaned_text = "\n".join(cleaned_lines)

    df = pd.read_csv(
        StringIO(cleaned_text),
        engine="python",
    )

    df.columns = df.columns.str.strip()

    unnamed_cols = [
        col for col in df.columns if str(col).startswith("Unnamed")
    ]

    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

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
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    df = df.copy()

    df["Region"] = df["Region"].astype(str).str.strip()
    df["Product"] = df["Product"].astype(str).str.strip()
    df["Product"] = df["Product"].replace(PRODUCT_ALIASES)

    invalid_regions = sorted(set(df["Region"].unique()) - set(REGIONS))
    invalid_products = sorted(set(df["Product"].unique()) - set(PRODUCTS))

    if invalid_regions:
        st.error(f"Invalid regions found in uploaded file: {invalid_regions}")
        st.stop()

    if invalid_products:
        st.error(f"Invalid products found in uploaded file: {invalid_products}")
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
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric_columns].isnull().any().any():
        st.error("Some numeric columns contain blank or invalid numeric values.")
        st.stop()

    return df


def show_bar(data, x_col, y_col, title, color_col=None):
    if color_col is None:
        color_col = x_col

    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        text=y_col,
        title=title,
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=420,
        showlegend=False,
        yaxis_title="Engineers",
        xaxis_title="",
        plot_bgcolor="white",
    )

    fig.update_xaxes(tickangle=-20)
    fig.update_yaxes(rangemode="tozero")

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )


def show_line(data, title):
    fig = px.line(
        data,
        x="Year",
        y="Engineers",
        color="Metric",
        markers=True,
        title=title,
    )

    fig.update_layout(
        height=420,
        yaxis_title="Engineers",
        plot_bgcolor="white",
    )

    fig.update_xaxes(dtick=1)
    fig.update_yaxes(rangemode="tozero")

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )


def build_functional_inputs(
    total_hiring,
    hiring_intensity_pct,
    peak_year,
    peak_hiring,
    product_exec,
    region_exec,
):
    inputs = []

    if total_hiring > 0:
        top_product_name = product_exec.iloc[0]["Product"]
        top_product_hiring = int(product_exec.iloc[0]["Hiring_SE"])

        top_region_name = region_exec.iloc[0]["Region"]
        top_region_hiring = int(region_exec.iloc[0]["Hiring_SE"])
    else:
        top_product_name = "Not applicable"
        top_product_hiring = 0

        top_region_name = "Not applicable"
        top_region_hiring = 0

    inputs.append(
        {
            "Function": "HR - Resource Planning",
            "Planning Input": (
                f"Prepare workforce plan for {total_hiring} additional SE across the selected forecast period. "
                f"Peak demand is expected in {peak_year} with {peak_hiring} SE. "
                "Plan hiring phasing, source mix, replacement backfill, onboarding calendar, and joining lead-time."
            ),
            "Focus Area": (
                f"Priority region: {top_region_name} ({top_region_hiring} SE). "
                f"Priority product: {top_product_name} ({top_product_hiring} SE)."
            ),
            "Timeline": "Immediate planning / monthly tracking",
        }
    )

    inputs.append(
        {
            "Function": "Technical Training Team - Competency Enhancement",
            "Planning Input": (
                "Create competency enhancement plan aligned to forecasted product and regional demand. "
                "Build training batches for new hires and existing engineers, including product certification, "
                "troubleshooting, safety practices, and field readiness."
            ),
            "Focus Area": (
                f"Prioritize {top_product_name} capability building and prepare training capacity before "
                f"{peak_year} peak demand."
            ),
            "Timeline": "0 - 60 days plan, quarterly execution",
        }
    )

    inputs.append(
        {
            "Function": "Operations Leaders - Budget Enhancement",
            "Planning Input": (
                "Plan budget enhancement for training, safety PPE, measuring tools, uniforms, branding, "
                "field kits, and onboarding readiness. Budget should support both new hiring and competency "
                "uplift of existing manpower."
            ),
            "Focus Area": (
                "Include training cost, certification cost, PPE sets, calibrated measuring instruments, "
                "uniforms, branding material, laptops/mobile tools if applicable, and regional deployment readiness."
            ),
            "Timeline": "Budget cycle / immediate approval for critical gaps",
        }
    )

    if hiring_intensity_pct >= 15:
        risk_priority = "High"
        risk_message = (
            "Hiring intensity is high versus current base. Budget and training capacity should be approved "
            "early to avoid delayed deployment and service delivery risk."
        )
    elif hiring_intensity_pct >= 8:
        risk_priority = "Medium"
        risk_message = (
            "Hiring intensity is moderate. Monthly tracking is required for hiring progress, training completion, "
            "and budget readiness."
        )
    else:
        risk_priority = "Controlled"
        risk_message = (
            "Hiring intensity is controlled. Continue monitoring demand, attrition, training pipeline, "
            "and budget utilization."
        )

    inputs.append(
        {
            "Function": "Executive Governance",
            "Planning Input": risk_message,
            "Focus Area": (
                f"Risk priority: {risk_priority}. Review hiring, training, safety readiness, tools availability, "
                "and budget status in monthly governance."
            ),
            "Timeline": "Monthly review",
        }
    )

    return inputs


# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
init_state()


# =====================================================
# SIDEBAR FORM
# =====================================================
st.sidebar.header("Planning Assumptions")
st.sidebar.markdown("Edit assumptions and click **Apply Assumptions**.")

with st.sidebar.form("planning_assumptions_form"):
    st.subheader("2027 Region and Product Wise Growth")

    edited_growth_dfs = {}

    for region in REGIONS:
        st.markdown(f"**{region} Growth**")

        edited_growth_dfs[region] = st.data_editor(
            growth_region_to_df(region),
            hide_index=True,
            use_container_width=True,
            disabled=["Product"],
            height=205,
            column_config={
                "BAU": st.column_config.NumberColumn(
                    "BAU ↑%",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                ),
                "DC": st.column_config.NumberColumn(
                    "DC ↑%",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                ),
            },
            key=f"growth_data_editor_{region.lower()}",
        )

    st.subheader("2028 and 2029 Regional Growth Multiplication Factors")
    st.caption(
        "Factors multiply the previous year's BAU/DC growth. "
        "Valid range: 0.1x to 10.0x."
    )

    edited_growth_factors_df = st.data_editor(
        growth_factors_to_df(),
        hide_index=True,
        use_container_width=True,
        disabled=["Region"],
        height=180,
        column_config={
            "2028 BAU Factor": st.column_config.NumberColumn(
                "2028 BAU x",
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                format="%.1f",
            ),
            "2028 DC Factor": st.column_config.NumberColumn(
                "2028 DC x",
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                format="%.1f",
            ),
            "2029 BAU Factor": st.column_config.NumberColumn(
                "2029 BAU x",
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                format="%.1f",
            ),
            "2029 DC Factor": st.column_config.NumberColumn(
                "2029 DC x",
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                format="%.1f",
            ),
        },
        key="growth_factors_data_editor",
    )

    st.subheader("BU Wise Attrition")

    edited_attrition_df = st.data_editor(
        attrition_to_df(),
        hide_index=True,
        use_container_width=True,
        disabled=["Product"],
        height=210,
        column_config={
            "Attr %": st.column_config.NumberColumn(
                "Attr %",
                min_value=0.0,
                max_value=30.0,
                step=0.5,
            )
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
            ),
            "Days/M": st.column_config.NumberColumn(
                "Days/M",
                min_value=1,
                max_value=31,
                step=1,
            ),
            "Util %": st.column_config.NumberColumn(
                "Util %",
                min_value=1.0,
                max_value=100.0,
                step=1.0,
            ),
        },
        key="productivity_data_editor",
    )

    apply_assumptions = st.form_submit_button("Apply Assumptions")

if apply_assumptions:
    st.session_state.growth_parameters = growth_region_dfs_to_dict(
        edited_growth_dfs
    )

    st.session_state.growth_factors = growth_factors_df_to_dict(
        edited_growth_factors_df
    )

    st.session_state.attrition_parameters = attrition_df_to_dict(
        edited_attrition_df
    )

    p = edited_productivity_df.iloc[0]

    st.session_state.productive_hours = float(p["Hrs/Day"])
    st.session_state.working_days = int(p["Days/M"])
    st.session_state.target_utilization = float(p["Util %"])
    st.session_state.needs_recalc = True

    st.sidebar.success("Assumptions applied. Dashboard will refresh.")


# =====================================================
# MAIN PAGE
# =====================================================
st.title("AI Enabled Workforce & Capacity Planning")
st.caption(f"Forecast model version: {MODEL_VERSION}")
st.info(
    "Upload workforce_input.csv and review workforce prediction for 2027, 2028 and 2029."
)

uploaded_file = st.file_uploader(
    "Upload workforce_input.csv",
    type=["csv"],
)

if uploaded_file is not None:
    current_file_id = f"{uploaded_file.name}_{len(uploaded_file.getvalue())}"

    if current_file_id != st.session_state.uploaded_file_id:
        try:
            st.session_state.input_df = validate_input_data(
                safe_read_csv(uploaded_file)
            )

            st.session_state.uploaded_file_id = current_file_id
            st.session_state.needs_recalc = True

            st.success("CSV uploaded successfully.")

        except Exception as error:
            st.error("CSV upload failed. Please check file format.")
            st.exception(error)
            st.stop()

if st.session_state.input_df is None:
    st.warning("Please upload workforce_input.csv to start workforce planning.")
    st.stop()

original_df = st.session_state.input_df


# =====================================================
# DASHBOARD FILTERS
# =====================================================
st.markdown("### Dashboard Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

filtered_df = original_df.copy()

with filter_col1:
    if "Year" in filtered_df.columns:
        base_years = (
            filtered_df["Year"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        )

        selected_base_years = st.multiselect(
            "Select Base Year",
            options=base_years,
            default=base_years,
        )

        filtered_df = filtered_df[
            filtered_df["Year"].astype(int).isin(selected_base_years)
        ]

    else:
        selected_base_years = ["All"]

with filter_col2:
    available_regions = [
        region for region in REGIONS if region in filtered_df["Region"].unique()
    ]

    selected_regions = st.multiselect(
        "Select Region",
        options=available_regions,
        default=available_regions,
    )

    filtered_df = filtered_df[
        filtered_df["Region"].isin(selected_regions)
    ]

with filter_col3:
    selected_forecast_years = st.multiselect(
        "Select Forecast Year",
        options=FORECAST_YEARS,
        default=FORECAST_YEARS,
    )

if filtered_df.empty:
    st.warning("No data available for selected Base Year / Region filter.")
    st.stop()

if not selected_forecast_years:
    st.warning("Please select at least one forecast year.")
    st.stop()

filter_signature = (
    tuple(selected_base_years),
    tuple(selected_regions),
    int(len(filtered_df)),
)

if st.session_state.last_filter_signature != filter_signature:
    st.session_state.needs_recalc = True
    st.session_state.last_filter_signature = filter_signature


# =====================================================
# CALCULATION
# =====================================================
if st.session_state.needs_recalc or st.session_state.result_df is None:
    try:
        st.session_state.result_df = calculate_workforce(
            df=filtered_df,
            growth_parameters=st.session_state.growth_parameters,
            growth_factors=st.session_state.growth_factors,
            attrition_parameters=st.session_state.attrition_parameters,
            productive_hours=st.session_state.productive_hours,
            working_days=st.session_state.working_days,
            target_utilization=st.session_state.target_utilization,
        )

        st.session_state.needs_recalc = False

    except Exception as error:
        st.error("Calculation failed. Please check workforce_model.py.")
        st.exception(error)
        st.stop()

result = st.session_state.result_df.copy()
result = result[result["Year"].isin(selected_forecast_years)]


# =====================================================
# DASHBOARD SUMMARY
# =====================================================
st.subheader("Dashboard Summary")

year_summary = (
    result.groupby("Year")
    .agg(
        Available=("Available Engineers", "sum"),
        BAU_Required=("BAU Required Engineers", "sum"),
        DC_Incremental=("DC Incremental Engineers", "sum"),
        Combined_Required=("Combined Required Engineers", "sum"),
        Additional_Required=("Combined Additional Required", "sum"),
    )
    .reset_index()
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric(
    "Existing 2026 SE",
    int(round(filtered_df["Current_SE"].sum(), 0)),
)

for metric_col, year in zip([kpi2, kpi3, kpi4], FORECAST_YEARS):
    year_row = year_summary[year_summary["Year"] == year]

    value = (
        int(year_row["Additional_Required"].sum())
        if not year_row.empty
        else 0
    )

    metric_col.metric(
        f"{year} Additional Required",
        value,
    )

kpi5.metric(
    "Selected Years Total Hiring",
    int(year_summary["Additional_Required"].sum()),
)


# =====================================================
# VISUAL DASHBOARD
# =====================================================
st.markdown("---")
st.subheader("Visual Dashboard")

trend_df = year_summary.melt(
    id_vars="Year",
    value_vars=[
        "Available",
        "Combined_Required",
        "Additional_Required",
    ],
    var_name="Metric",
    value_name="Engineers",
)

trend_df["Metric"] = trend_df["Metric"].replace(
    {
        "Available": "Available Engineers",
        "Combined_Required": "Combined Required Engineers",
        "Additional_Required": "Additional Required",
    }
)

trend_df["Engineers"] = trend_df["Engineers"].round(0)

show_line(
    trend_df,
    "Three-Year Workforce Forecast Trend",
)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    product_required = (
        result.groupby("Product")["Combined Required Engineers"]
        .sum()
        .reset_index()
    )

    show_bar(
        product_required,
        "Product",
        "Combined Required Engineers",
        "Selected Years Required SE by Product",
        "Product",
    )

with chart_col2:
    region_required = (
        result.groupby("Region")["Combined Required Engineers"]
        .sum()
        .reset_index()
    )

    show_bar(
        region_required,
        "Region",
        "Combined Required Engineers",
        "Selected Years Required SE by Region",
        "Region",
    )

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    product_hiring = (
        result.groupby("Product")["Combined Additional Required"]
        .sum()
        .reset_index()
    )

    show_bar(
        product_hiring,
        "Product",
        "Combined Additional Required",
        "Selected Years Additional Requirement by Product",
        "Product",
    )

with chart_col4:
    region_hiring = (
        result.groupby("Region")["Combined Additional Required"]
        .sum()
        .reset_index()
    )

    show_bar(
        region_hiring,
        "Region",
        "Combined Additional Required",
        "Selected Years Additional Requirement by Region",
        "Region",
    )


# =====================================================
# DETAIL TABS
# =====================================================
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Executive Summary",
        "Input Data",
        "Full Results",
        "BU Requirement Comparison",
        "Yearly Tables",
        "Growth Factors",
        "Download",
    ]
)

with tab0:
    st.subheader("Executive Summary - Executive View")

    total_existing = int(round(filtered_df["Current_SE"].sum(), 0))
    total_hiring = int(round(year_summary["Additional_Required"].sum(), 0))
    selected_years_text = ", ".join(
        [str(year) for year in selected_forecast_years]
    )

    final_year = max(selected_forecast_years)
    final_year_row = year_summary[year_summary["Year"] == final_year]

    final_required = (
        int(round(final_year_row["Combined_Required"].sum(), 0))
        if not final_year_row.empty
        else 0
    )

    final_available = (
        int(round(final_year_row["Available"].sum(), 0))
        if not final_year_row.empty
        else 0
    )

    peak_year_row = year_summary.sort_values(
        "Additional_Required",
        ascending=False,
    ).iloc[0]

    peak_year = int(peak_year_row["Year"])
    peak_hiring = int(round(peak_year_row["Additional_Required"], 0))

    final_growth_pct = (
        ((final_required - total_existing) / total_existing) * 100
        if total_existing > 0
        else 0
    )

    hiring_intensity_pct = (
        (total_hiring / total_existing) * 100
        if total_existing > 0
        else 0
    )

    if hiring_intensity_pct >= 15:
        capacity_status = "High expansion requirement"
        status_message = (
            "The forecast indicates a material capacity build-up requirement. "
            "Leadership attention is recommended for hiring phasing, onboarding "
            "bandwidth, and regional deployment readiness."
        )

    elif hiring_intensity_pct >= 8:
        capacity_status = "Moderate expansion requirement"
        status_message = (
            "The forecast indicates a controlled but visible manpower increase. "
            "Hiring actions should be planned early to avoid capacity constraints "
            "in peak demand periods."
        )

    else:
        capacity_status = "Controlled requirement"
        status_message = (
            "The forecast indicates a manageable workforce requirement. Current "
            "capacity and planned hiring appear broadly aligned with the selected "
            "assumptions."
        )

    exec_kpi1, exec_kpi2, exec_kpi3, exec_kpi4 = st.columns(4)

    exec_kpi1.metric("Current Base SE", total_existing)
    exec_kpi2.metric(f"{final_year} Required SE", final_required)
    exec_kpi3.metric("Total Hiring Need", total_hiring)
    exec_kpi4.metric("Peak Hiring Year", f"{peak_year} ({peak_hiring} SE)")

    st.markdown("---")

    st.markdown(
        f"""
        ### Leadership Readout

        For the selected forecast period **{selected_years_text}**, the current installed service engineering base is **{total_existing} SE**.

        The projected requirement by **{final_year}** is **{final_required} SE**, compared with **{final_available} SE** available after attrition before hiring.

        The model projects a total additional hiring requirement of **{total_hiring} SE**, with the highest annual hiring need in **{peak_year}** at **{peak_hiring} SE**.

        **Executive interpretation:** **{capacity_status}**. {status_message}

        **Strategic implication:** The forecasted final-year requirement represents approximately **{final_growth_pct:.0f}%** movement versus the current base. The selected-year total hiring intensity is approximately **{hiring_intensity_pct:.0f}%** of the current base.
        """
    )

    st.markdown("### Year-wise Workforce Outlook")

    year_summary_display = year_summary.copy()

    numeric_cols = [
        "Available",
        "BAU_Required",
        "DC_Incremental",
        "Combined_Required",
        "Additional_Required",
    ]

    year_summary_display[numeric_cols] = (
        year_summary_display[numeric_cols]
        .round(0)
        .astype(int)
    )

    year_summary_display = year_summary_display.rename(
        columns={
            "Available": "Available SE After Attrition",
            "BAU_Required": "BAU Required SE",
            "DC_Incremental": "DC Incremental SE",
            "Combined_Required": "Combined Required SE",
            "Additional_Required": "Additional Hiring SE",
        }
    )

    st.dataframe(
        year_summary_display,
        use_container_width=True,
    )

    product_exec = (
        result.groupby("Product")
        .agg(
            Required_SE=("Combined Required Engineers", "sum"),
            Hiring_SE=("Combined Additional Required", "sum"),
        )
        .reset_index()
    )

    product_exec[["Required_SE", "Hiring_SE"]] = (
        product_exec[["Required_SE", "Hiring_SE"]]
        .round(0)
        .astype(int)
    )

    product_exec = product_exec.sort_values(
        "Hiring_SE",
        ascending=False,
    )

    region_exec = (
        result.groupby("Region")
        .agg(
            Required_SE=("Combined Required Engineers", "sum"),
            Hiring_SE=("Combined Additional Required", "sum"),
        )
        .reset_index()
    )

    region_exec[["Required_SE", "Hiring_SE"]] = (
        region_exec[["Required_SE", "Hiring_SE"]]
        .round(0)
        .astype(int)
    )

    region_exec = region_exec.sort_values(
        "Hiring_SE",
        ascending=False,
    )

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown("### Product Prioritization")

        st.dataframe(
            product_exec.rename(
                columns={
                    "Required_SE": "Selected Years Required SE",
                    "Hiring_SE": "Selected Years Hiring SE",
                }
            ),
            use_container_width=True,
        )

    with summary_col2:
        st.markdown("### Regional Prioritization")

        st.dataframe(
            region_exec.rename(
                columns={
                    "Required_SE": "Selected Years Required SE",
                    "Hiring_SE": "Selected Years Hiring SE",
                }
            ),
            use_container_width=True,
        )

    st.markdown("### Executive Action Notes")

    if total_hiring > 0:
        top_product_name = product_exec.iloc[0]["Product"]
        top_product_hiring = int(product_exec.iloc[0]["Hiring_SE"])

        top_region_name = region_exec.iloc[0]["Region"]
        top_region_hiring = int(region_exec.iloc[0]["Hiring_SE"])

        st.warning(
            f"Highest product-level hiring pressure is in **{top_product_name}** "
            f"with **{top_product_hiring} SE**. Highest regional hiring pressure "
            f"is in **{top_region_name}** with **{top_region_hiring} SE**. "
            f"Recommended executive-level actions: validate growth assumptions with "
            f"business leaders, phase hiring by quarter, confirm onboarding "
            f"capacity, and review cross-region redeployment options before "
            f"external hiring commitment."
        )

    else:
        st.success(
            "No additional hiring requirement is projected under the selected "
            "assumptions. Recommended executive-level action: validate whether growth, "
            "attrition, and DC assumptions are realistic, because zero hiring may "
            "indicate either sufficient capacity or conservative workload assumptions."
        )

    st.markdown("---")
    st.markdown("### Functional Inputs for Execution Planning")

    input_col1, input_col2, input_col3 = st.columns(3)

    input_col1.metric("Total Resource Ask", total_hiring)
    input_col2.metric("Peak Demand Year", peak_year)
    input_col3.metric("Peak Year Resource Ask", peak_hiring)

    functional_inputs = build_functional_inputs(
        total_hiring=total_hiring,
        hiring_intensity_pct=hiring_intensity_pct,
        peak_year=peak_year,
        peak_hiring=peak_hiring,
        product_exec=product_exec,
        region_exec=region_exec,
    )

    functional_input_df = pd.DataFrame(functional_inputs)

    st.dataframe(
        functional_input_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Functional Action Guidance")

    st.markdown(
        "- **HR:** convert forecasted SE requirement into region-wise and product-wise hiring, "
        "backfill, and onboarding plan."
    )

    st.markdown(
        "- **Technical Training Team:** prepare competency enhancement roadmap for product capability, "
        "certification, troubleshooting, safety practices, and field readiness."
    )

    st.markdown(
        "- **Operations Leaders:** plan budget enhancement for training, safety PPE, measuring tools, "
        "uniforms, branding, field kits, and deployment readiness."
    )

    st.markdown(
        "- **Executive Governance:** review monthly progress for hiring, training completion, "
        "PPE/tools readiness, and budget approvals."
    )

with tab1:
    st.subheader("Uploaded Input Data")

    st.dataframe(
        filtered_df,
        use_container_width=True,
    )

with tab2:
    st.subheader("Workforce Planning Results")

    st.dataframe(
        result,
        use_container_width=True,
    )

with tab3:
    st.subheader("BU Requirement Comparison")

    existing = (
        filtered_df.groupby("Product")["Current_SE"]
        .sum()
        .reset_index()
        .rename(columns={"Current_SE": "Existing 2026 SE"})
    )

    required = (
        result.pivot_table(
            values="Combined Required Engineers",
            index="Product",
            columns="Year",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    required = required.rename(
        columns={
            year: f"{year} Required SE"
            for year in FORECAST_YEARS
        }
    )

    comparison = existing.merge(
        required,
        on="Product",
        how="outer",
    ).fillna(0)

    if "2029 Required SE" in comparison.columns:
        comparison["2029 Gap / Surplus"] = (
            comparison["2029 Required SE"]
            - comparison["Existing 2026 SE"]
        ).round(1)

        comparison["2029 Additional Required"] = comparison[
            "2029 Gap / Surplus"
        ].apply(
            lambda value: max(math.ceil(value), 0)
        )

    st.dataframe(
        comparison.round(0),
        use_container_width=True,
    )

with tab4:
    st.subheader("Yearly Requirement Tables")

    for year in selected_forecast_years:
        year_result = result[result["Year"] == year]

        st.markdown(f"### {year} Combined BAU + DC Requirement Table")

        combined_table = year_result.pivot_table(
            values="Combined Required Engineers",
            index="Product",
            columns="Region",
            fill_value=0,
            aggfunc="sum",
        )

        st.dataframe(
            add_total_row_and_column(combined_table).round(0),
            use_container_width=True,
        )

        st.markdown(f"### {year} Combined Hiring Requirement Table")

        hiring_table = year_result.pivot_table(
            values="Combined Additional Required",
            index="Product",
            columns="Region",
            fill_value=0,
            aggfunc="sum",
        )

        st.dataframe(
            add_total_row_and_column(hiring_table).round(0),
            use_container_width=True,
        )

with tab5:
    st.subheader("Growth Factors Used for 2028 and 2029")

    st.dataframe(
        growth_factors_to_df(),
        use_container_width=True,
    )

    st.subheader("Effective BAU/DC Growth by Year")

    st.dataframe(
        result[
            [
                "Region",
                "Product",
                "Year",
                "BAU Growth %",
                "DC Growth %",
            ]
        ].drop_duplicates(),
        use_container_width=True,
    )

with tab6:
    st.subheader("Download Output")

    csv_output = result.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Workforce Planning Output 2027-2029",
        data=csv_output,
        file_name="workforce_planning_output_2027_2028_2029.csv",
        mime="text/csv",
    )
