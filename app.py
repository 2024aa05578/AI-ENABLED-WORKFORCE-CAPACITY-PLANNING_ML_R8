import copy
import math
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

from workforce_model import calculate_workforce

st.set_page_config(page_title="AI Enabled Workforce & Capacity Planning", page_icon="🚀", layout="wide")

REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Products", "Power System", "Industrial Automation"]
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

PRODUCT_REVERSE_DISPLAY = {v: k for k, v in PRODUCT_DISPLAY.items()}

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

DEFAULT_ATTRITION = {product: 8.0 for product in PRODUCTS}

APP_SCHEMA_VERSION = "v16_three_year_rolling_forecast"


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


def growth_region_to_df(region):
    return pd.DataFrame(
        [
            {
                "Product": PRODUCT_DISPLAY[p],
                "BAU": float(st.session_state.growth_parameters[region][p]["BAU"]),
                "DC": float(st.session_state.growth_parameters[region][p]["DC"]),
            }
            for p in PRODUCTS
        ]
    )


def growth_region_dfs_to_dict(edited_growth_dfs):
    values = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)

    for region, growth_df in edited_growth_dfs.items():
        for _, row in growth_df.iterrows():
            product = PRODUCT_REVERSE_DISPLAY.get(str(row["Product"]).strip())

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
        row.update(st.session_state.growth_factors.get(region, DEFAULT_GROWTH_FACTORS[region]))
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
    return pd.DataFrame(
        [
            {
                "Product": PRODUCT_DISPLAY[p],
                "Attr %": float(st.session_state.attrition_parameters[p]),
            }
            for p in PRODUCTS
        ]
    )


def attrition_df_to_dict(attrition_df):
    values = copy.deepcopy(DEFAULT_ATTRITION)

    for _, row in attrition_df.iterrows():
        product = PRODUCT_REVERSE_DISPLAY.get(str(row["Product"]).strip())

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

    df = pd.read_csv(StringIO(cleaned_text), engine="python")
    df.columns = df.columns.str.strip()

    unnamed_cols = [col for col in df.columns if str(col).startswith("Unnamed")]

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

    missing_columns = [c for c in required_columns if c not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    df = df.copy()

    df["Region"] = df["Region"].astype(str).str.strip()
    df["Product"] = df["Product"].astype(str).str.strip().replace(PRODUCT_ALIASES)

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

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

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
        texttemplate="%{text:.1f}",
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
    st.caption("Factors multiply the previous year's BAU/DC growth. Valid range: 0.1x to 10.0x.")

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
    st.session_state.growth_parameters = growth_region_dfs_to_dict(edited_growth_dfs)
    st.session_state.growth_factors = growth_factors_df_to_dict(edited_growth_factors_df)
    st.session_state.attrition_parameters = attrition_df_to_dict(edited_attrition_df)

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
st.info("Upload workforce_input.csv and review workforce prediction for 2027, 2028 and 2029.")

uploaded_file = st.file_uploader("Upload workforce_input.csv", type=["csv"])

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
        r for r in REGIONS if r in filtered_df["Region"].unique()
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
    round(filtered_df["Current_SE"].sum(), 1),
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

show_line(
    trend_df,
    "Three-Year Workforce Forecast Trend",
)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    show_bar(
        result.groupby("Product")["Combined Required Engineers"]
        .sum()
        .reset_index(),
        "Product",
        "Combined Required Engineers",
        "Selected Years Required SE by Product",
        "Product",
    )

with chart_col2:
    show_bar(
        result.groupby("Region")["Combined Required Engineers"]
        .sum()
        .reset_index(),
        "Region",
        "Combined Required Engineers",
        "Selected Years Required SE by Region",
        "Region",
    )

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    show_bar(
        result.groupby("Product")["Combined Additional Required"]
        .sum()
        .reset_index(),
        "Product",
        "Combined Additional Required",
        "Selected Years Additional Requirement by Product",
        "Product",
    )

with chart_col4:
    show_bar(
        result.groupby("Region")["Combined Additional Required"]
        .sum()
        .reset_index(),
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
    st.subheader("Executive Summary")
    st.dataframe(
        year_summary.round(1),
        use_container_width=True,
    )

    if int(year_summary["Additional_Required"].sum()) > 0:
        top_product = (
            result.groupby("Product")["Combined Additional Required"]
            .sum()
            .sort_values(ascending=False)
        )

        top_region = (
            result.groupby("Region")["Combined Additional Required"]
            .sum()
            .sort_values(ascending=False)
        )

        peak_year = year_summary.sort_values(
            "Additional_Required",
            ascending=False,
        ).iloc[0]

        st.warning(
            f"Highest additional requirement is in **{top_product.index[0]}** "
            f"with **{int(top_product.iloc[0])} SE**. "
            f"Region-wise highest requirement is in **{top_region.index[0]}** "
            f"with **{int(top_region.iloc[0])} SE**. "
            f"Peak hiring year is **{int(peak_year['Year'])}** "
            f"with **{int(peak_year['Additional_Required'])} SE**."
        )
    else:
        st.success(
            "No additional hiring requirement is currently projected for selected filters."
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
        comparison.round(1),
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
            add_total_row_and_column(combined_table).round(1),
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
            add_total_row_and_column(hiring_table).round(1),
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
