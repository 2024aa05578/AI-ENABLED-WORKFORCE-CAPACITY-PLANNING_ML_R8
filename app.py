import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="SE Workforce Forecast - Leadership View", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#f2f6ff,#eefaf3,#fff8ec);border-right:1px solid #d8e1ef}.pane-title{font-size:20px;font-weight:800;color:#222b45}.pane-note{font-size:13px;color:#5d6678}.region-card{background:white;border-radius:14px;padding:12px;margin:15px 0 8px 0;box-shadow:0 3px 14px rgba(33,48,90,.08);border:1px solid #e3e9f5}.north{border-left:7px solid #4f7cff}.west{border-left:7px solid #ff9f43}.south{border-left:7px solid #20c997}.east{border-left:7px solid #a066ff}.region-title{font-weight:800;color:#252a34}.region-sub{font-size:12px;color:#697386}.app-title{font-size:31px;font-weight:850;color:#252a34}.app-sub{font-size:14px;color:#687386;margin-bottom:20px}.section-header{font-size:23px;font-weight:850;color:#2c3140;margin-top:24px;margin-bottom:12px}.kpi-wrap{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:12px 0 28px}.kpi{background:white;border-radius:17px;padding:21px 23px;box-shadow:0 5px 20px rgba(30,45,90,.09);border:1px solid #edf0f7}.blue{border-top:7px solid #4f7cff;background:linear-gradient(180deg,#f5f8ff,#fff)}.purple{border-top:7px solid #8e5cff;background:linear-gradient(180deg,#faf7ff,#fff)}.orange{border-top:7px solid #ff9f43;background:linear-gradient(180deg,#fff8ef,#fff)}.kpi-label{font-size:13px;color:#687386;font-weight:700}.kpi-value{font-size:36px;color:#242936;font-weight:850}.callout{background:linear-gradient(135deg,#eef4ff,#f8f0ff,#fff8ec);border:1px solid #dfe7ff;border-left:9px solid #4f7cff;border-radius:20px;padding:23px 28px;margin:16px 0 28px;box-shadow:0 6px 24px rgba(41,65,120,.1)}.callout-title{font-size:24px;font-weight:850;color:#242936}.callout li{margin-bottom:10px;font-size:15px;color:#303747;line-height:1.58}.hi{font-weight:850;color:#1f5eff}.warn{font-weight:850;color:#d97706}.ok{font-weight:850;color:#0f9f6e}.strip{background:#f7f9fc;border:1px solid #e7ecf5;border-radius:14px;padding:14px 18px;margin-bottom:18px;color:#3c4658;font-size:14px}div.stButton>button{background:linear-gradient(90deg,#4f7cff,#20c997);color:white;border:none;border-radius:11px;font-weight:800;width:100%}
</style>
""", unsafe_allow_html=True)

FORECAST_YEARS = [2027, 2028, 2029]
REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Prod", "Power Sys"]

PRODUCT_DISPLAY_MAP = {
    "UPS": "UPS",
    "Cooling": "Cooling",
    "Power Prod": "Power Product",
    "Power Sys": "Power System",
}

STYLE_MAP = {
    "North": "north",
    "West": "west",
    "South": "south",
    "East": "east",
}

BASE_SE = pd.DataFrame(
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

DEFAULT_BAU = {
    region: {product: 10 for product in PRODUCTS}
    for region in REGIONS
}

DEFAULT_DC = {
    "North": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
    "West": {"UPS": 4, "Cooling": 4, "Power Prod": 2, "Power Sys": 2},
    "South": {"UPS": 2, "Cooling": 2, "Power Prod": 0, "Power Sys": 0},
    "East": {"UPS": 0, "Cooling": 0, "Power Prod": 0, "Power Sys": 0},
}


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(round(float(value)))
    except Exception:
        return default


def growth_df(region):
    return pd.DataFrame(
        {
            "Product": PRODUCTS,
            "BAU ^%": [DEFAULT_BAU[region][product] for product in PRODUCTS],
            "DC ^%": [DEFAULT_DC[region][product] for product in PRODUCTS],
        }
    )


def region_card(region):
    st.markdown(
        f"""
        <div class="region-card {STYLE_MAP[region]}">
            <div class="region-title">{region} Growth</div>
            <div class="region-sub">Product-wise BAU and DC growth assumptions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_excel(sheets):
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
        rows = []

        for _, base_row in self.base_df.iterrows():
            region = base_row["Region"]
            product = base_row["Product"]

            previous_required = to_float(base_row["Current SE"])
            previous_available = to_float(base_row["Current SE"])

            for year in FORECAST_YEARS:
                growth_table = self.growth_inputs.get(region, pd.DataFrame())

                if "Product" in growth_table.columns:
                    product_row = growth_table[growth_table["Product"] == product]
                else:
                    product_row = pd.DataFrame()

                if product_row.empty:
                    bau_growth = 0.0
                    dc_growth = 0.0
                else:
                    bau_growth = to_float(product_row["BAU ^%"].iloc[0])
                    dc_growth = to_float(product_row["DC ^%"].iloc[0])

                attrition = to_float(self.attrition_inputs.get(year, 0))

                available_after_attrition = previous_available * (1 - attrition / 100)
                bau_required = previous_required * (1 + bau_growth / 100)
                dc_incremental = previous_required * dc_growth / 100
                combined_required = bau_required + dc_incremental
                hiring_need = max(combined_required - available_after_attrition, 0)
                closing_available = available_after_attrition + hiring_need

                rows.append(
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

        detailed = pd.DataFrame(rows)
        selected = detailed[detailed["Year"].isin(self.selected_years)].copy()

        yearwise = self.make_yearwise(selected)
        product_priority = self.make_priority(selected, "Product Display", "Product")
        regional_priority = self.make_priority(selected, "Region", "Region")
        bu_comparison = self.make_bu(selected)
        growth_factors = self.make_growth_factors()
        summary = self.make_summary(yearwise)

        return (
            summary,
            detailed,
            yearwise,
            product_priority,
            regional_priority,
            bu_comparison,
            growth_factors,
        )

    def make_yearwise(self, selected):
        df = selected.groupby("Year", as_index=False).agg(
            {
                "Available SE After Attrition": "sum",
                "BAU Required SE": "sum",
                "DC Incremental SE": "sum",
                "Combined Required SE": "sum",
                "Hiring Need": "sum",
                "Closing Available SE": "sum",
            }
        )

        value_cols = [column for column in df.columns if column != "Year"]
        df[value_cols] = df[value_cols].round(0).astype(int)

        return df

    def make_priority(self, selected, group_col, label_col):
        df = selected.groupby(group_col, as_index=False).agg(
            {
                "Combined Required SE": "sum",
                "Hiring Need": "sum",
            }
        )

        df = df.rename(
            columns={
                group_col: label_col,
                "Combined Required SE": "Selected Years Required SE",
                "Hiring Need": "Selected Years Hiring SE",
            }
        )

        df[["Selected Years Required SE", "Selected Years Hiring SE"]] = df[
            ["Selected Years Required SE", "Selected Years Hiring SE"]
        ].round(0).astype(int)

        if label_col == "Product":
            df["Product"] = df["Product"].replace(PRODUCT_DISPLAY_MAP)

        return df.sort_values("Selected Years Required SE", ascending=False)

    def make_bu(self, selected):
        df = selected.groupby(["Region", "Product Display"], as_index=False).agg(
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
            ascending=[True, False],
        )

    def make_growth_factors(self):
        rows = []

        for region in REGIONS:
            table = self.growth_inputs.get(region, pd.DataFrame())

            for _, row in table.iterrows():
                product = row.get("Product", "")

                rows.append(
                    {
                        "Region": region,
                        "Product": PRODUCT_DISPLAY_MAP.get(product, product),
                        "BAU Growth %": to_float(row.get("BAU ^%", 0)),
                        "DC Growth %": to_float(row.get("DC ^%", 0)),
                    }
                )

        return pd.DataFrame(rows)

    def make_summary(self, yearwise):
        current_base = to_int(self.base_df["Current SE"].sum())
        final_year = max(self.selected_years)

        final_row = yearwise[yearwise["Year"] == final_year].iloc[0]

        final_required = to_int(final_row["Combined Required SE"])
        available_final = to_int(final_row["Available SE After Attrition"])
        total_hiring = to_int(yearwise["Hiring Need"].sum())

        high_row = yearwise.sort_values("Hiring Need", ascending=False).iloc[0]

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
            "highest_annual_hiring_year": to_int(high_row["Year"]),
            "highest_annual_hiring_need": to_int(high_row["Hiring Need"]),
            "final_year_growth_vs_current_base_pct": growth_pct,
            "total_hiring_intensity_pct": hiring_intensity,
            "interpretation": interpretation,
        }


with st.sidebar:
    st.markdown(
        """
        <div class="pane-title">Planning Assumptions</div>
        <div class="pane-note">Edit assumptions and click <b>Apply Assumptions</b>.</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Forecast Years")

    selected_years = st.multiselect(
        "Select forecast years",
        FORECAST_YEARS,
        default=FORECAST_YEARS,
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
            key=f"attr_{year}",
        )

    st.markdown("#### Region and Product Wise Growth")

    growth_inputs = {}

    for region in REGIONS:
        region_card(region)

        growth_inputs[region] = st.data_editor(
            growth_df(region),
            hide_index=True,
            use_container_width=True,
            key=f"growth_{region}",
        )

    st.button("Apply Assumptions")


model = WorkforceForecastModel(
    BASE_SE,
    growth_inputs,
    attrition_inputs,
    selected_years,
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


summary_tab, input_tab, full_tab, bu_tab, yearly_tab, growth_tab, download_tab = st.tabs(
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


with summary_tab:
    st.markdown(
        """
        <div class="app-title">Executive Summary - Leadership View</div>
        <div class="app-sub">
            Headcount-based workforce forecast covering service engineering capacity,
            attrition-adjusted availability, required SE, hiring need, product priority,
            and regional priority.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-wrap">
            <div class="kpi blue">
                <div class="kpi-label">Current Base SE</div>
                <div class="kpi-value">{summary['current_base_se']}</div>
            </div>
            <div class="kpi purple">
                <div class="kpi-label">{summary['final_year']} Required SE</div>
                <div class="kpi-value">{summary['final_year_required_se']}</div>
            </div>
            <div class="kpi orange">
                <div class="kpi-label">Total Hiring Need</div>
                <div class="kpi-value">{summary['total_hiring_need']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        f"""
        <div class="callout">
            <div class="callout-title">Leadership Readout</div>
            <ul>
                <li>Forecast period selected: <span class="hi">{', '.join(map(str, summary['selected_years']))}</span>.</li>
                <li>Current installed service engineering base: <span class="hi">{summary['current_base_se']} SE</span>.</li>
                <li>Projected requirement by <span class="hi">{summary['final_year']}</span>: <span class="hi">{summary['final_year_required_se']} SE</span>.</li>
                <li>Available SE after attrition before hiring by <span class="hi">{summary['final_year']}</span>: <span class="hi">{summary['available_after_attrition_final_year']} SE</span>.</li>
                <li>Total additional hiring required across selected years: <span class="warn">{summary['total_hiring_need']} SE</span>.</li>
                <li>Highest annual hiring requirement is in <span class="warn">{summary['highest_annual_hiring_year']}</span> with <span class="warn">{summary['highest_annual_hiring_need']} SE</span>.</li>
                <li>Leadership interpretation: <span class="warn">{summary['interpretation']}</span>.</li>
                <li>Strategic implication: Final-year requirement is approximately <span class="hi">{summary['final_year_growth_vs_current_base_pct']}%</span> movement versus current base, and selected-year hiring intensity is approximately <span class="hi">{summary['total_hiring_intensity_pct']}%</span> of current base.</li>
                <li>Recommended focus: <span class="ok">hiring phasing, onboarding bandwidth, delivery readiness, utilization balance, and regional deployment capacity.</span></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-header">Year-wise Workforce Outlook</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        yearwise_df,
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns([1.35, 1])

    with col1:
        st.markdown(
            '<div class="section-header">Product Prioritization</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            product_priority_df,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown(
            '<div class="section-header">Regional Prioritization</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            regional_priority_df,
            use_container_width=True,
            hide_index=True,
        )


with input_tab:
    st.markdown(
        '<div class="section-header">Input Data</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Current Base SE")

    st.dataframe(
        BASE_SE,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Selected Forecast Years")
    st.write(sorted(selected_years))

    st.markdown("#### Attrition Assumptions")

    st.dataframe(
        pd.DataFrame(
            {
                "Year": list(attrition_inputs.keys()),
                "Attrition %": list(attrition_inputs.values()),
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


with full_tab:
    st.markdown(
        '<div class="section-header">Full Results</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="strip">
            Full result table shows each region-product-year combination with opening base,
            attrition-adjusted availability, BAU requirement, DC incremental requirement,
            combined requirement, hiring need, and closing available SE.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        detailed_df,
        use_container_width=True,
        hide_index=True,
    )


with bu_tab:
    st.markdown(
        '<div class="section-header">BU Requirement Comparison</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        bu_comparison_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Pivot View: Region x Product")

    pivot_required = bu_comparison_df.pivot_table(
        index="Region",
        columns="Product",
        values="Selected Years Required SE",
        aggfunc="sum",
        fill_value=0,
    )

    st.dataframe(
        pivot_required,
        use_container_width=True,
    )


with yearly_tab:
    st.markdown(
        '<div class="section-header">Yearly Tables</div>',
        unsafe_allow_html=True,
    )

    for year in FORECAST_YEARS:
        st.markdown(f"#### {year}")

        st.dataframe(
            detailed_df[detailed_df["Year"] == year].copy(),
            use_container_width=True,
            hide_index=True,
        )


with growth_tab:
    st.markdown(
        '<div class="section-header">Growth Factors</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="strip">
            Growth factors are taken from the left planning pane.
            BAU growth drives normal requirement expansion.
            DC growth is treated as incremental demand on top of BAU requirement.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        growth_factor_df,
        use_container_width=True,
        hide_index=True,
    )


with download_tab:
    st.markdown(
        '<div class="section-header">Download</div>',
        unsafe_allow_html=True,
    )

    sheets = {
        "Executive Summary": pd.DataFrame([summary]),
        "Yearwise Outlook": yearwise_df,
        "Product Priority": product_priority_df,
        "Regional Priority": regional_priority_df,
        "BU Comparison": bu_comparison_df,
        "Full Results": detailed_df,
        "Growth Factors": growth_factor_df,
        "Input Base SE": BASE_SE,
    }

    st.download_button(
        label="Download Workforce Forecast Excel",
        data=make_excel(sheets),
        file_name="v17_headcount_based_forecast_leadership_view.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("#### Preview of Download Sheets")
    st.write(list(sheets.keys()))
