import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="SE Workforce Forecast - Leadership View",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background-color: #ffffff; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#f2f6ff 0%,#eefaf3 55%,#fff8ec 100%);
    border-right: 1px solid #d8e1ef;
}

.left-pane-heading {
    font-size: 20px;
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
    background: #fff;
    border-radius: 14px;
    padding: 13px 14px;
    margin-top: 16px;
    margin-bottom: 10px;
    box-shadow: 0 3px 14px rgba(33,48,90,.08);
    border: 1px solid #e3e9f5;
}

.region-card-north { border-left: 7px solid #4f7cff; }
.region-card-west { border-left: 7px solid #ff9f43; }
.region-card-south { border-left: 7px solid #20c997; }
.region-card-east { border-left: 7px solid #a066ff; }

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
    background: linear-gradient(90deg,#4f7cff 0%,#20c997 100%);
    color: white;
    border: none;
    border-radius: 11px;
    font-weight: 800;
    width: 100%;
}

div.stButton > button:hover {
    background: linear-gradient(90deg,#3d66d6 0%,#17a884 100%);
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
    grid-template-columns: repeat(3,1fr);
    gap: 18px;
    margin-top: 12px;
    margin-bottom: 28px;
}

.kpi-card {
    background: #fff;
    border-radius: 17px;
    padding: 21px 23px;
    box-shadow: 0 5px 20px rgba(30,45,90,.09);
    border: 1px solid #edf0f7;
}

.kpi-card-blue {
    border-top: 7px solid #4f7cff;
    background: linear-gradient(180deg,#f5f8ff 0%,#fff 100%);
}

.kpi-card-purple {
    border-top: 7px solid #8e5cff;
    background: linear-gradient(180deg,#faf7ff 0%,#fff 100%);
}

.kpi-card-orange {
    border-top: 7px solid #ff9f43;
    background: linear-gradient(180deg,#fff8ef 0%,#fff 100%);
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
    background: linear-gradient(135deg,#eef4ff 0%,#f8f0ff 45%,#fff8ec 100%);
    border: 1px solid #dfe7ff;
    border-left: 9px solid #4f7cff;
    border-radius: 20px;
    padding: 23px 28px;
    margin: 16px 0 28px 0;
    box-shadow: 0 6px 24px rgba(41,65,120,.10);
}

.leadership-callout-title {
    font-size: 24px;
    font-weight: 850;
    color: #242936;
    margin-bottom: 13px;
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
</style>
""", unsafe_allow_html=True)


FORECAST_YEARS = [2027, 2028, 2029]
REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Prod", "Power Sys"]

PRODUCT_DISPLAY_MAP = {
    "UPS": "UPS",
    "Cooling": "Cooling",
    "Power Prod": "Power Product",
    "Power Sys": "Power System"
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
    columns=["Region", "Product", "Current SE"]
)

DEFAULT_ATTRITION = {
    2027: 5.0,
    2028: 5.0,
    2029: 5.0
}

DEFAULT_BAU_GROWTH = {
    region: {product: 10 for product in PRODUCTS}
    for region in REGIONS
}

DEFAULT_DC_GROWTH = {
    "North": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
    "West": {"UPS": 4, "Cooling": 4, "Power Prod": 2, "Power Sys": 2},
    "South": {"UPS": 2, "Cooling": 2, "Power Prod": 0, "Power Sys": 0},
    "East": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
}


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


def pct_multiplier(pct):
    return 1 + safe_float(pct, 0) / 100


def build_growth_df(region):
    return pd.DataFrame(
        {
            "Product": PRODUCTS,
            "BAU ^%": [DEFAULT_BAU_GROWTH[region][product] for product in PRODUCTS],
            "DC ^%": [DEFAULT_DC_GROWTH[region][product] for product in PRODUCTS],
        }
    )


def region_card(region, css_class):
    st.markdown(
        f"""
        <div class="region-card {css_class}">
            <div class="region-card-title">{region} Growth</div>
            <div class="region-card-subtitle">Product-wise BAU and DC growth assumptions</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def excel_bytes(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


class WorkforceForecastModel:
    def __init__(self, base_df, growth_inputs, attrition_inputs, selected_years):
        self.base_df = base_df.copy()
        self.growth_inputs = growth_inputs
        self.attrition_inputs = attrition_inputs
        self.selected_years = sorted(selected_years)

    def run(self):
        detail_rows = []

        for _, base_row in self.base_df.iterrows():
            region = base_row["Region"]
            product = base_row["Product"]
            current_se = safe_float(base_row["Current SE"], 0)

            previous_required = current_se
            previous_available = current_se

            for year in FORECAST_YEARS:
                growth_table = self.growth_inputs.get(region, pd.DataFrame())

                if "Product" in growth_table.columns:
                    product_rows = growth_table[growth_table["Product"] == product]
                else:
                    product_rows = pd.DataFrame()

                if product_rows.empty:
                    bau_growth = 0.0
                    dc_growth = 0.0
                else:
                    bau_growth = safe_float(product_rows["BAU ^%"].iloc[0], 0)
                    dc_growth = safe_float(product_rows["DC ^%"].iloc[0], 0)

                attrition = safe_float(self.attrition_inputs.get(year, 0), 0)

                available_after_attrition = previous_available * (1 - attrition / 100)
                bau_required = previous_required * pct_multiplier(bau_growth)
                dc_incremental = previous_required * (dc_growth / 100)
                combined_required = bau_required + dc_incremental
                hiring_need = max(combined_required - available_after_attrition, 0)
                closing_available = available_after_attrition + hiring_need

                detail_rows.append(
                    {
                        "Year": year,
                        "Region": region,
                        "Product": product,
                        "Product Display": PRODUCT_DISPLAY_MAP.get(product, product),
                        "Opening SE Base": round(previous_available, 2),
                        "Attrition %": attrition,
                        "Available SE After Attrition": round(available_after_attrition, 2),
                        "BAU Growth %": bau_growth,
                        "DC Growth %": dc_growth,
                        "BAU Required SE": round(bau_required, 2),
                        "DC Incremental SE": round(dc_incremental, 2),
                        "Combined Required SE": round(combined_required, 2),
                        "Hiring Need": round(hiring_need, 2),
                        "Closing Available SE": round(closing_available, 2),
                    }
                )

                previous_required = combined_required
                previous_available = closing_available

        detailed_df = pd.DataFrame(detail_rows)
        selected_df = detailed_df[detailed_df["Year"].isin(self.selected_years)].copy()

        yearwise_df = self.yearwise(selected_df)
        product_df = self.priority(selected_df, "Product Display", "Product")
        region_df = self.priority(selected_df, "Region", "Region")
        bu_df = self.bu_comparison(selected_df)
        growth_df = self.growth_factors()
        summary = self.summary(yearwise_df)

        return summary, detailed_df, yearwise_df, product_df, region_df, bu_df, growth_df

    def yearwise(self, selected_df):
        df = selected_df.groupby("Year", as_index=False).agg(
            {
                "Available SE After Attrition": "sum",
                "BAU Required SE": "sum",
                "DC Incremental SE": "sum",
                "Combined Required SE": "sum",
                "Hiring Need": "sum",
                "Closing Available SE": "sum",
            }
        )

        num_cols = [column for column in df.columns if column != "Year"]
        df[num_cols] = df[num_cols].round(0).astype(int)

        return df

    def priority(self, selected_df, group_col, rename_to):
        df = selected_df.groupby(group_col, as_index=False).agg(
            {
                "Combined Required SE": "sum",
                "Hiring Need": "sum",
            }
        )

        df = df.rename(
            columns={
                group_col: rename_to,
                "Combined Required SE": "Selected Years Required SE",
                "Hiring Need": "Selected Years Hiring SE",
            }
        )

        df[["Selected Years Required SE", "Selected Years Hiring SE"]] = df[
            ["Selected Years Required SE", "Selected Years Hiring SE"]
        ].round(0).astype(int)

        if rename_to == "Product":
            df["Product"] = df["Product"].replace(PRODUCT_DISPLAY_MAP)

        return df.sort_values("Selected Years Required SE", ascending=False)

    def bu_comparison(self, selected_df):
        df = selected_df.groupby(["Region", "Product Display"], as_index=False).agg(
            {
                "Combined Required SE": "sum",
                "Hiring Need": "sum",
            }
        )

        df = df.rename(
            columns={
                "Product Display": "Product",
                "Combined Required SE": "Selected Years Required SE",
                "Hiring Need": "Selected Years Hiring SE",
            }
        )

        df[["Selected Years Required SE", "Selected Years Hiring SE"]] = df[
            ["Selected Years Required SE", "Selected Years Hiring SE"]
        ].round(0).astype(int)

        return df.sort_values(
            ["Region", "Selected Years Required SE"],
            ascending=[True, False]
        )

    def growth_factors(self):
        rows = []

        for region in REGIONS:
            table = self.growth_inputs.get(region, pd.DataFrame())

            for _, row in table.iterrows():
                product = row.get("Product", "")

                rows.append(
                    {
                        "Region": region,
                        "Product": PRODUCT_DISPLAY_MAP.get(product, product),
                        "BAU Growth %": safe_float(row.get("BAU ^%", 0), 0),
                        "DC Growth %": safe_float(row.get("DC ^%", 0), 0),
                    }
                )

        return pd.DataFrame(rows)

    def summary(self, yearwise_df):
        current_base = safe_int(self.base_df["Current SE"].sum())
        final_year = max(self.selected_years)

        final_row = yearwise_df[yearwise_df["Year"] == final_year].iloc[0]

        final_required = safe_int(final_row["Combined Required SE"])
        available_final = safe_int(final_row["Available SE After Attrition"])
        total_hiring = safe_int(yearwise_df["Hiring Need"].sum())

        high_row = yearwise_df.sort_values("Hiring Need", ascending=False).iloc[0]

        if current_base:
            growth_pct = round(((final_required - current_base) / current_base) * 100)
            hiring_intensity = round((total_hiring / current_base) * 100)
        else:
            growth_pct = 0
            hiring_intensity = 0

        if hiring_intensity >= 150:
            interpretation = "High expansion requirement"
        elif hiring_intensity >= 75:
            interpretation = "Moderate to high expansion requirement"
        else:
            interpretation = "Controlled expansion requirement"

        return {
            "current_base_se": current_base,
            "selected_years": self.selected_years,
            "final_year": final_year,
            "final_year_required_se": final_required,
            "available_after_attrition_final_year": available_final,
            "total_hiring_need": total_hiring,
            "highest_annual_hiring_year": safe_int(high_row["Year"]),
            "highest_annual_hiring_need": safe_int(high_row["Hiring Need"]),
            "final_year_growth_vs_current_base_pct": growth_pct,
            "total_hiring_intensity_pct": hiring_intensity,
            "interpretation": interpretation,
        }


with st.sidebar:
    st.markdown(
        """
        <div class="left-pane-heading">Planning Assumptions</div>
        <div class="left-pane-caption">Edit assumptions and click <b>Apply Assumptions</b>.</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### Forecast Years")

    selected_years = st.multiselect(
        "Select forecast years",
        FORECAST_YEARS,
        default=FORECAST_YEARS
    )

    if not selected_years:
        selected_years = FORECAST_YEARS

    st.markdown("#### Attrition Assumptions")

    attrition_inputs = {}

    for year in FORECAST_YEARS:
        attrition_inputs[year] = st.number_input(
            f"{year} Attrition %",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_ATTRITION[year],
            step=0.5,
            key=f"attr_{year}"
        )

    st.markdown("#### Region and Product Wise Growth")

    growth_inputs = {}

    style_map = {
        "North": "region-card-north",
        "West": "region-card-west",
        "South": "region-card-south",
        "East": "region-card-east"
    }

    for region in REGIONS:
        region_card(region, style_map[region])

        growth_inputs[region] = st.data_editor(
            build_growth_df(region),
            hide_index=True,
            use_container_width=True,
            key=f"growth_{region}"
        )

    st.button("Apply Assumptions")


model = WorkforceForecastModel(
    DEFAULT_BASE_SE,
    growth_inputs,
    attrition_inputs,
    selected_years
)

(
    summary,
    detailed_df,
    yearwise_df,
    product_priority_df,
    regional_priority_df,
    bu_comparison_df,
    growth_factor_df,
) = model.run()


tabs = st.tabs(
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


with tabsst.markdown(
        """
        <div class="app-title">Executive Summary - Leadership View</div>
        <div class="app-subtitle">
            Headcount-based workforce forecast covering service engineering capacity,
            attrition-adjusted availability, required SE, hiring need, product priority,
            and regional priority.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card kpi-card-blue">
                <div class="kpi-label">Current Base SE</div>
                <div class="kpi-value">{summary['current_base_se']}</div>
            </div>
            <div class="kpi-card kpi-card-purple">
                <div class="kpi-label">{summary['final_year']} Required SE</div>
                <div class="kpi-value">{summary['final_year_required_se']}</div>
            </div>
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-label">Total Hiring Need</div>
                <div class="kpi-value">{summary['total_hiring_need']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        f"""
        <div class="leadership-callout">
            <div class="leadership-callout-title">Leadership Readout</div>
            <ul>
                <li>
                    Forecast period selected:
                    <span class="leadership-highlight">{', '.join(map(str, summary['selected_years']))}</span>.
                </li>
                <li>
                    Current installed service engineering base:
                    <span class="leadership-highlight">{summary['current_base_se']} SE</span>.
                </li>
                <li>
                    Projected requirement by
                    <span class="leadership-highlight">{summary['final_year']}</span>:
                    <span class="leadership-highlight">{summary['final_year_required_se']} SE</span>.
                </li>
                <li>
                    Available SE after attrition before hiring by
                    <span class="leadership-highlight">{summary['final_year']}</span>:
                    <span class="leadership-highlight">{summary['available_after_attrition_final_year']} SE</span>.
                </li>
                <li>
                    Total additional hiring required across selected years:
                    <span class="leadership-warning">{summary['total_hiring_need']} SE</span>.
                </li>
                <li>
                    Highest annual hiring requirement is in
                    <span class="leadership-warning">{summary['highest_annual_hiring_year']}</span>
                    with
                    <span class="leadership-warning">{summary['highest_annual_hiring_need']} SE</span>.
                </li>
                <li>
                    Leadership interpretation:
                    <span class="leadership-warning">{summary['interpretation']}</span>.
                </li>
                <li>
                    Strategic implication:
                    Final-year requirement represents approximately
                    <span class="leadership-highlight">{summary['final_year_growth_vs_current_base_pct']}%</span>
                    movement versus current base, while selected-year hiring intensity is approximately
                    <span class="leadership-highlight">{summary['total_hiring_intensity_pct']}%</span>
                    of the current base.
                </li>
                <li>
                    Recommended focus:
                    <span class="leadership-success">
                        hiring phasing, onboarding bandwidth, delivery readiness,
                        utilization balance, and regional deployment capacity.
                    </span>
                </li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-header">Year-wise Workforce Outlook</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        yearwise_df,
        use_container_width=True,
        hide_index=True
    )

    col1, col2 = st.columns([1.35, 1])

    with col1:
        st.markdown(
            '<div class="section-header">Product Prioritization</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            product_priority_df,
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown(
            '<div class="section-header">Regional Prioritization</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            regional_priority_df,
            use_container_width=True,
            hide_index=True
        )


with tabsst.markdown(
        '<div class="section-header">Input Data</div>',
        unsafe_allow_html=True
    )

    st.markdown("#### Current Base SE")

    st.dataframe(
        DEFAULT_BASE_SE,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Selected Forecast Years")
    st.write(sorted(selected_years))

    st.markdown("#### Attrition Assumptions")

    attrition_df = pd.DataFrame(
        {
            "Year": list(attrition_inputs.keys()),
            "Attrition %": list(attrition_inputs.values()),
        }
    )

    st.dataframe(
        attrition_df,
        use_container_width=True,
        hide_index=True
    )


with tabsst.markdown(
        '<div class="section-header">Full Results</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="metric-strip">
            Full result table shows each region-product-year combination with opening base,
            attrition-adjusted availability, BAU requirement, DC incremental requirement,
            combined requirement, hiring need, and closing available SE.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.dataframe(
        detailed_df,
        use_container_width=True,
        hide_index=True
    )


with tabsst.markdown(
        '<div class="section-header">BU Requirement Comparison</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        bu_comparison_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Pivot View: Region x Product")

    pivot_required = bu_comparison_df.pivot_table(
        index="Region",
        columns="Product",
        values="Selected Years Required SE",
        aggfunc="sum",
        fill_value=0
    )

    st.dataframe(
        pivot_required,
        use_container_width=True
    )


with tabsst.markdown(
        '<div class="section-header">Yearly Tables</div>',
        unsafe_allow_html=True
    )

    for year in FORECAST_YEARS:
        st.markdown(f"#### {year}")

        year_df = detailed_df[detailed_df["Year"] == year].copy()

        st.dataframe(
            year_df,
            use_container_width=True,
            hide_index=True
        )


with tabsst.markdown(
        '<div class="section-header">Growth Factors</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="metric-strip">
            Growth factors are taken from the left planning pane.
            BAU growth drives normal requirement expansion.
            DC growth is treated as incremental demand on top of BAU requirement.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.dataframe(
        growth_factor_df,
        use_container_width=True,
        hide_index=True
    )


with tabsst.markdown(
        '<div class="section-header">Download</div>',
        unsafe_allow_html=True
    )

    sheets = {
        "Executive Summary": pd.DataFrame([summary]),
        "Yearwise Outlook": yearwise_df,
        "Product Priority": product_priority_df,
        "Regional Priority": regional_priority_df,
        "BU Comparison": bu_comparison_df,
        "Full Results": detailed_df,
        "Growth Factors": growth_factor_df,
        "Input Base SE": DEFAULT_BASE_SE,
    }

    st.download_button(
        label="Download Workforce Forecast Excel",
        data=excel_bytes(sheets),
        file_name="v17_headcount_based_forecast_leadership_view.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("#### Preview of Download Sheets")
    st.write(list(sheets.keys()))
