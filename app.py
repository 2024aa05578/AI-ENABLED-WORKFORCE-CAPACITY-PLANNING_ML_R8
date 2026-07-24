import copy
import math
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

from workforce_model import calculate_workforce

st.set_page_config(page_title="AI Enabled Workforce & Capacity Planning", page_icon="rocket", layout="wide")

UP_ARROW = chr(8593)
BAU_UP_LABEL = "BAU " + UP_ARROW + "%"
DC_UP_LABEL = "DC " + UP_ARROW + "%"
FORECAST_YEARS = [2027, 2028, 2029]

st.markdown("""
<style>
section[data-testid="stSidebar"] {width: 380px !important; min-width: 380px !important; max-width: 380px !important; background: linear-gradient(180deg,#F8FAFC 0%,#EEF4FA 100%);} 
section[data-testid="stSidebar"] > div {width: 380px !important; min-width: 380px !important; max-width: 380px !important; padding-left: 6px !important; padding-right: 6px !important;}
div[data-testid="stSidebarContent"] {width: 380px !important; max-width: 380px !important;}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {font-size: 12px !important; margin-top: 5px !important; margin-bottom: 3px !important; color: #1F4E79 !important;}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div {font-size: 9px !important; line-height: 1.1 !important;}
section[data-testid="stSidebar"] button {font-size: 10px !important; padding-top: 3px !important; padding-bottom: 3px !important; background-color: #1F4E79 !important; color: white !important; border-radius: 6px !important;}
.region-header {padding: 5px 8px; border-radius: 7px; margin-top: 6px; margin-bottom: 4px; font-weight: 700; font-size: 11px;}
.sidebar-note {font-size: 9px; color: #475569; padding: 5px 7px; border-radius: 6px; background: #EAF2F8; border-left: 3px solid #1F4E79; margin-bottom: 6px;}
</style>
""", unsafe_allow_html=True)

REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Products", "Power System", "Industrial Automation"]

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
    value: key
    for key, value in PRODUCT_DISPLAY.items()
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
    2027: {
        "H1": 60.0,
        "H2": 40.0,
    },
    2028: {
        "H1": 50.0,
        "H2": 50.0,
    },
    2029: {
        "H1": 50.0,
        "H2": 50.0,
    },
}

APP_SCHEMA_VERSION = "v21_variable_dc_yearwise"


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
                "DC 2027": float(
                    dc_values.get(
                        2027,
                        dc_values.get("2027", 0.0),
                    )
                ),
                "DC 2028": float(
                    dc_values.get(
                        2028,
                        dc_values.get("2028", 0.0),
                    )
                ),
                "DC 2029": float(
                    dc_values.get(
                        2029,
                        dc_values.get("2029", 0.0),
                    )
                ),
            }
        )

    return pd.DataFrame(rows)


def growth_region_dfs_to_dict(edited_growth_dfs):
    output = copy.deepcopy(DEFAULT_GROWTH_PARAMETERS)

    for region, growth_df in edited_growth_dfs.items():
        for _, row in growth_df.iterrows():
            product = PRODUCT_REVERSE_DISPLAY.get(
                str(row["Product"]).strip()
            )

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
    return pd.DataFrame(
        [
            {
                "Product": PRODUCT_DISPLAY[product],
                "Attr %": float(attrition_parameters.get(product, 8.0)),
            }
            for product in PRODUCTS
        ]
    )


def attrition_df_to_dict(attrition_df):
    output = copy.deepcopy(DEFAULT_ATTRITION)

    for _, row in attrition_df.iterrows():
        product = PRODUCT_REVERSE_DISPLAY.get(
            str(row["Product"]).strip()
        )

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
    return pd.DataFrame(
        [
            {
                "Forecast Year": year,
                "H1 %": float(split_parameters[year]["H1"]),
                "H2 %": float(split_parameters[year]["H2"]),
            }
            for year in FORECAST_YEARS
        ]
    )


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

    unnamed = [
        column for column in df.columns
        if str(column).startswith("Unnamed")
    ]

    if unnamed:
        df = df.drop(columns=unnamed)

    return df


def validate_input_data(df):
    required = [
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

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    df = df.copy()

    df["Region"] = df["Region"].astype(str).str.strip()
    df["Product"] = (
        df["Product"]
        .astype(str)
        .str.strip()
        .replace(PRODUCT_ALIASES)
    )

    bad_regions = sorted(
        set(df["Region"].unique()) - set(REGIONS)
    )

    bad_products = sorted(
        set(df["Product"].unique()) - set(PRODUCTS)
    )

    if bad_regions:
        st.error(f"Invalid regions found: {bad_regions}")
        st.stop()

    if bad_products:
        st.error(f"Invalid products found: {bad_products}")
        st.stop()

    numeric = [
        "Current_SE",
        "Breakdown_WO",
        "Breakdown_Hrs",
        "PM_WO",
        "PM_Hrs",
        "Startup_WO",
        "Startup_Hrs",
    ]

    if "Year" in df.columns:
        numeric.append("Year")

    for column in numeric:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric].isnull().any().any():
        st.error("Some numeric columns contain blank or invalid numeric values.")
        st.stop()

    return df


def show_bar_chart_with_values(data, x_col, y_col, title, color_col=None):
    data = data.copy()
    data[y_col] = data[y_col].round(0)

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
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=430,
        title_x=0.05,
        showlegend=False,
        margin=dict(
            l=40,
            r=30,
            t=70,
            b=90,
        ),
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


def make_display_df(dataframe):
    display_df = dataframe.copy()

    numeric_columns = display_df.select_dtypes(
        include=["number"]
    ).columns

    for column in numeric_columns:
        display_df[column] = display_df[column].round(0).astype("Int64")

    return display_df


def apply_feedback_correction(result, feedback_df):
    adjusted = result.copy()
    adjusted["ML Correction Factor"] = 1.0
    adjusted["ML Adjusted Required SE"] = adjusted["Combined Required Engineers"]

    if feedback_df is None or feedback_df.empty:
        return adjusted, pd.DataFrame()

    feedback_df = feedback_df.copy()

    required = [
        "Forecast Year",
        "Region",
        "Product",
        "System Forecast SE",
        "Manual Forecast SE",
    ]

    if any(column not in feedback_df.columns for column in required):
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
        feedback_df
        .groupby(["Region", "Product"])["Correction Factor"]
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
                "Combined Required Engineers": "System Forecast SE",
            }
        )
        .assign(
            **{
                "Manual Forecast SE": "",
                "Remarks": "",
            }
        )
    )


init_state()

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
                    width=92,
                ),
                "BAU": st.column_config.NumberColumn(
                    BAU_UP_LABEL,
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=42,
                ),
                "DC 2027": st.column_config.NumberColumn(
                    "DC27 " + UP_ARROW + "%",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=44,
                ),
                "DC 2028": st.column_config.NumberColumn(
                    "DC28 " + UP_ARROW + "%",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=44,
                ),
                "DC 2029": st.column_config.NumberColumn(
                    "DC29 " + UP_ARROW + "%",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    width=44,
                ),
            },
            key=f"growth_data_editor_{region.lower()}",
        )

    st.subheader("BU Wise Attrition")

    edited_attrition_df = st.data_editor(
        attrition_dict_to_df(
            st.session_state.attrition_parameters,
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
            st.session_state.hiring_split_parameters,
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
        edited_growth_dfs,
    )

    st.session_state.attrition_parameters = attrition_df_to_dict(
        edited_attrition_df,
    )

    st.session_state.hiring_split_parameters = hiring_split_df_to_dict(
        edited_hiring_split_df,
    )

    (
        st.session_state.productive_hours,
        st.session_state.working_days,
        st.session_state.target_utilization,
    ) = productivity_df_to_values(
        edited_productivity_df,
    )

    st.session_state.needs_recalc = True
    st.sidebar.success("Assumptions applied. Dashboard will refresh.")


st.title("AI Enabled Workforce & Capacity Planning")

st.info(
    "Upload workforce_input.csv, update assumptions, review 3-year forecast, "
    "H1/H2 hiring, and ML feedback."
)

uploaded_file = st.file_uploader(
    "Upload workforce_input.csv",
    type=["csv"],
)

if uploaded_file is not None:
    current_file_id = f"{uploaded_file.name}_{len(uploaded_file.getvalue())}"

    if current_file_id != st.session_state.uploaded_file_id:
        raw_df = safe_read_csv(uploaded_file)
        st.session_state.input_df = validate_input_data(raw_df)
        st.session_state.uploaded_file_id = current_file_id
        st.session_state.needs_recalc = True
        st.success("CSV uploaded successfully.")


if st.session_state.input_df is None:
    st.warning("Please upload workforce_input.csv to start workforce planning.")
    st.stop()


original_df = st.session_state.input_df

st.markdown("### Dashboard Filters")

filter_col1, filter_col2 = st.columns(2)

filtered_df = original_df.copy()

with filter_col1:
    if "Year" in filtered_df.columns:
        available_years = (
            filtered_df["Year"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        )

        selected_years = st.multiselect(
            "Select Baseline Year",
            options=available_years,
            default=available_years,
        )

        filtered_df = filtered_df[
            filtered_df["Year"].astype(int).isin(selected_years)
        ]

    else:
        selected_years = ["All"]

with filter_col2:
    available_regions = [
        region for region in REGIONS
        if region in filtered_df["Region"].unique()
    ]

    selected_regions = st.multiselect(
        "Select Region",
        options=available_regions,
        default=available_regions,
    )

    filtered_df = filtered_df[
        filtered_df["Region"].isin(selected_regions)
    ]


if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()


df = filtered_df

filter_signature = (
    tuple(selected_years),
    tuple(selected_regions),
    int(len(df)),
    tuple(
        (
            year,
            st.session_state.hiring_split_parameters[year]["H1"],
            st.session_state.hiring_split_parameters[year]["H2"],
        )
        for year in FORECAST_YEARS
    ),
)

if st.session_state.last_filter_signature != filter_signature:
    st.session_state.needs_recalc = True
    st.session_state.last_filter_signature = filter_signature


if st.session_state.needs_recalc or st.session_state.result_df is None:
    result = calculate_workforce(
        df=df,
        growth_parameters=st.session_state.growth_parameters,
        attrition_parameters=st.session_state.attrition_parameters,
        productive_hours=st.session_state.productive_hours,
        working_days=st.session_state.working_days,
        target_utilization=st.session_state.target_utilization,
        forecast_years=FORECAST_YEARS,
        hiring_split_parameters=st.session_state.hiring_split_parameters,
    )

    st.session_state.result_df = result
    st.session_state.needs_recalc = False

else:
    result = st.session_state.result_df


st.subheader("Dashboard Summary")

total_current = int(round(df["Current_SE"].sum(), 0))
final_year = max(FORECAST_YEARS)

final_required = int(
    round(
        result[
            result["Forecast Year"] == final_year
        ]["Combined Required Engineers"].sum(),
        0,
    )
)

total_hiring = int(
    round(
        result["Combined Additional Required"].sum(),
        0,
    )
)

total_h1 = int(
    round(
        result["H1 Hiring"].sum(),
        0,
    )
)

total_h2 = int(
    round(
        result["H2 Hiring"].sum(),
        0,
    )
)

summary_cols = st.columns(5)

summary_cols[0].metric("Baseline SE", total_current)
summary_cols[1].metric(f"{final_year} Required SE", final_required)
summary_cols[2].metric("3-Year Hiring", total_hiring)
summary_cols[3].metric("H1 Hiring Total", total_h1)
summary_cols[4].metric("H2 Hiring Total", total_h2)


st.markdown("---")
st.subheader("Visual Dashboard")

st.markdown("### Base Line Dashboard")

base1, base2 = st.columns(2)

with base1:
    base_product = (
        df.groupby("Product")["Current_SE"]
        .sum()
        .reset_index()
        .rename(columns={"Current_SE": "Existing SE"})
    )

    show_bar_chart_with_values(
        base_product,
        "Product",
        "Existing SE",
        "Base Line Existing Resource by Product",
        "Product",
    )

with base2:
    base_region = (
        df.groupby("Region")["Current_SE"]
        .sum()
        .reset_index()
        .rename(columns={"Current_SE": "Existing SE"})
    )

    show_bar_chart_with_values(
        base_region,
        "Region",
        "Existing SE",
        "Base Line Existing Resource by Region",
        "Region",
    )


st.markdown("### 3-Year Forecast Dashboard")

year_req = (
    result.groupby("Forecast Year")["Combined Required Engineers"]
    .sum()
    .reset_index()
)

year_hiring = (
    result.groupby("Forecast Year")[["H1 Hiring", "H2 Hiring"]]
    .sum()
    .reset_index()
)

c1, c2 = st.columns(2)

with c1:
    show_bar_chart_with_values(
        year_req,
        "Forecast Year",
        "Combined Required Engineers",
        "Required SE by Forecast Year",
        "Forecast Year",
    )

with c2:
    fig = px.bar(
        year_hiring,
        x="Forecast Year",
        y=["H1 Hiring", "H2 Hiring"],
        barmode="group",
        text_auto=True,
        title="Hiring Plan by Year: H1 and H2",
    )

    fig.update_layout(
        height=430,
        xaxis_title="",
        yaxis_title="Hiring",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        fixedrange=True,
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
        },
    )


c3, c4 = st.columns(2)

with c3:
    product_year = (
        result.groupby(["Forecast Year", "Product"])["Combined Required Engineers"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        product_year,
        x="Forecast Year",
        y="Combined Required Engineers",
        color="Product",
        markers=True,
        title="Product-wise Requirement Trend",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )

with c4:
    region_year = (
        result.groupby(["Forecast Year", "Region"])["Combined Required Engineers"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        region_year,
        x="Forecast Year",
        y="Combined Required Engineers",
        color="Region",
        markers=True,
        title="Region-wise Requirement Trend",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


feedback_file = None
ml_adjusted_result = result.copy()
ml_factors = pd.DataFrame()


tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Executive Summary",
        "3-Year Forecast",
        "Hiring Plan H1-H2",
        "ML Feedback",
        "Input Data",
        "Full Results",
        "DC and Combined",
        "Download",
    ]
)


with tab0:
    st.subheader("Executive Summary")

    selected_year_text = (
        ", ".join([str(year) for year in selected_years])
        if selected_years
        else "All"
    )

    selected_region_text = (
        ", ".join(selected_regions)
        if selected_regions
        else "All"
    )

    st.markdown(
        f"Current view: **Baseline Year = {selected_year_text}**, "
        f"**Region = {selected_region_text}**."
    )

    exec_cols = st.columns(4)

    exec_cols[0].metric("Baseline SE", total_current)
    exec_cols[1].metric(f"{final_year} Required SE", final_required)
    exec_cols[2].metric("3-Year Hiring", total_hiring)
    exec_cols[3].metric("H1 / H2 Hiring", f"{total_h1} / {total_h2}")

    st.markdown(
        "The system now provides a rolling 3-year forecast, splits annual hiring "
        "into H1 and H2, and captures manual forecast feedback for ML-based correction."
    )

    st.markdown("### Year-wise Summary")

    year_summary = (
        result.groupby("Forecast Year")
        .agg(
            Required_SE=("Combined Required Engineers", "sum"),
            Additional_Required=("Combined Additional Required", "sum"),
            H1_Hiring=("H1 Hiring", "sum"),
            H2_Hiring=("H2 Hiring", "sum"),
            Closing_SE=("Closing SE", "sum"),
        )
        .reset_index()
    )

    st.dataframe(
        make_display_df(year_summary),
        use_container_width=True,
    )


with tab1:
    st.subheader("3-Year Forecast")

    st.dataframe(
        make_display_df(result),
        use_container_width=True,
    )


with tab2:
    st.subheader("Hiring Plan H1-H2")

    hiring_plan = (
        result.groupby(["Forecast Year", "Region", "Product"])[
            [
                "Combined Additional Required",
                "H1 Hiring",
                "H2 Hiring",
            ]
        ]
        .sum()
        .reset_index()
    )

    st.dataframe(
        make_display_df(hiring_plan),
        use_container_width=True,
    )


with tab3:
    st.subheader("ML Feedback")

    st.info(
        "Upload manual-approved forecasts here. The app computes correction factors "
        "by Region + Product and shows an ML-adjusted view."
    )

    template = build_feedback_template(result)

    st.download_button(
        "Download ML Feedback Template",
        data=template.to_csv(index=False).encode("utf-8"),
        file_name="ml_feedback_template.csv",
        mime="text/csv",
    )

    feedback_upload = st.file_uploader(
        "Upload completed ML feedback CSV",
        type=["csv"],
        key="ml_feedback_upload",
    )

    if feedback_upload is not None:
        feedback_df = safe_read_csv(feedback_upload)

        ml_adjusted_result, ml_factors = apply_feedback_correction(
            result,
            feedback_df,
        )

        st.markdown("### Learned correction factors")

        st.dataframe(
            make_display_df(ml_factors),
            use_container_width=True,
        )

        st.markdown("### ML Adjusted Forecast")

        st.dataframe(
            make_display_df(ml_adjusted_result),
            use_container_width=True,
        )

    else:
        st.dataframe(
            make_display_df(template),
            use_container_width=True,
        )


with tab4:
    st.subheader("Uploaded Input Data")

    st.dataframe(
        make_display_df(df),
        use_container_width=True,
    )


with tab5:
    st.subheader("Full Results")

    st.dataframe(
        make_display_df(result),
        use_container_width=True,
    )


with tab6:
    st.subheader("DC Addition Requirement Table")

    dc_table = result.pivot_table(
        values="DC Incremental Engineers",
        index="Product",
        columns=["Forecast Year", "Region"],
        fill_value=0,
        aggfunc="sum",
    )

    st.dataframe(
        make_display_df(dc_table),
        use_container_width=True,
    )

    st.subheader("Combined Hiring Requirement Table")

    hiring_table = result.pivot_table(
        values="Combined Additional Required",
        index="Product",
        columns=["Forecast Year", "Region"],
        fill_value=0,
        aggfunc="sum",
    )

    st.dataframe(
        make_display_df(hiring_table),
        use_container_width=True,
    )


with tab7:
    st.subheader("Download Output")

    st.download_button(
        "Download 3-Year Forecast Output",
        data=make_display_df(result).to_csv(index=False).encode("utf-8"),
        file_name="three_year_workforce_forecast.csv",
        mime="text/csv",
    )

    hiring_download = result[
        [
            "Forecast Year",
            "Region",
            "Product",
            "Combined Additional Required",
            "H1 Hiring",
            "H2 Hiring",
        ]
    ]

    st.download_button(
        "Download Hiring Plan",
        data=make_display_df(hiring_download).to_csv(index=False).encode("utf-8"),
        file_name="h1_h2_hiring_plan.csv",
        mime="text/csv",
    )
