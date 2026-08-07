import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="SE Workforce Forecast - Leadership View", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
<style>
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#f2f6ff,#eefaf3,#fff8ec);border-right:1px solid #d8e1ef}
.title{font-size:30px;font-weight:800;color:#252a34}.sub{font-size:14px;color:#687386;margin-bottom:18px}.hdr{font-size:23px;font-weight:800;color:#2c3140;margin-top:22px;margin-bottom:10px}
.region{background:white;border-radius:12px;padding:12px;margin:14px 0 8px;border:1px solid #e3e9f5;box-shadow:0 3px 12px rgba(33,48,90,.08)}.north{border-left:7px solid #4f7cff}.west{border-left:7px solid #ff9f43}.south{border-left:7px solid #20c997}.east{border-left:7px solid #a066ff}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:12px 0 25px}.kpi{background:white;border-radius:16px;padding:20px;box-shadow:0 5px 18px rgba(30,45,90,.09);border:1px solid #edf0f7}.blue{border-top:7px solid #4f7cff}.purple{border-top:7px solid #8e5cff}.orange{border-top:7px solid #ff9f43}.kpi-label{font-size:13px;color:#687386;font-weight:700}.kpi-value{font-size:36px;font-weight:850;color:#242936}
.callout{background:linear-gradient(135deg,#eef4ff,#f8f0ff,#fff8ec);border-left:9px solid #4f7cff;border-radius:18px;padding:22px 26px;margin:14px 0 25px;box-shadow:0 6px 22px rgba(41,65,120,.10)}.callout li{margin-bottom:9px;line-height:1.55}.hi{font-weight:850;color:#1f5eff}.warn{font-weight:850;color:#d97706}.ok{font-weight:850;color:#0f9f6e}
.strip{background:#f7f9fc;border:1px solid #e7ecf5;border-radius:12px;padding:13px;margin-bottom:16px;color:#3c4658}div.stButton>button{background:linear-gradient(90deg,#4f7cff,#20c997);color:white;border:none;border-radius:10px;font-weight:800;width:100%}
</style>
''', unsafe_allow_html=True)

YEARS = [2027, 2028, 2029]
REGIONS = ["North", "West", "South", "East"]
PRODUCTS = ["UPS", "Cooling", "Power Prod", "Power Sys"]

PRODUCT_NAME = {
    "UPS": "UPS",
    "Cooling": "Cooling",
    "Power Prod": "Power Product",
    "Power Sys": "Power System",
}

REGION_STYLE = {
    "North": "north",
    "West": "west",
    "South": "south",
    "East": "east",
}

DEFAULT_BASE = pd.DataFrame(
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
    region: {product: 10.0 for product in PRODUCTS}
    for region in REGIONS
}

DEFAULT_DC = {
    "North": {"UPS": 0.0, "Cooling": 0.0, "Power Prod": 0.0, "Power Sys": 0.0},
    "West": {"UPS": 4.0, "Cooling": 4.0, "Power Prod": 2.0, "Power Sys": 2.0},
    "South": {"UPS": 2.0, "Cooling": 2.0, "Power Prod": 0.0, "Power Sys": 0.0},
    "East": {"UPS": 0.0, "Cooling": 0.0, "Power Prod": 0.0, "Power Sys": 0.0},
}


def num(x, default=0.0):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def whole(x):
    return int(round(num(x, 0)))


def growth_template(region):
    return pd.DataFrame(
        {
            "Product": PRODUCTS,
            "BAU %": [DEFAULT_BAU[region][product] for product in PRODUCTS],
            "DC %": [DEFAULT_DC[region][product] for product in PRODUCTS],
        }
    )


def load_csv(file):
    if file is None:
        return DEFAULT_BASE.copy(), "Using default base SE data."

    try:
        df = pd.read_csv(file)

        required = ["Region", "Product", "Current SE"]
        missing = [column for column in required if column not in df.columns]

        if missing:
            return DEFAULT_BASE.copy(), "Upload ignored. Missing columns: " + ", ".join(missing)

        df = df[required].copy()
        df["Region"] = df["Region"].astype(str).str.strip()
        df["Product"] = df["Product"].astype(str).str.strip()
        df["Current SE"] = pd.to_numeric(df["Current SE"], errors="coerce").fillna(0)

        df = df[df["Region"].isin(REGIONS) & df["Product"].isin(PRODUCTS)]

        if df.empty:
            return DEFAULT_BASE.copy(), "Upload ignored. No valid Region/Product rows found."

        df = df.groupby(["Region", "Product"], as_index=False)["Current SE"].sum()

        return df, "Using uploaded CSV base SE data."

    except Exception as error:
        return DEFAULT_BASE.copy(), "Upload failed. Using default data. Error: " + str(error)


def to_excel(sheets):
    out = BytesIO()

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)

    return out.getvalue()


def run_model(base_df, growth_inputs, attrition_inputs, selected_years):
    rows = []

    for _, base_row in base_df.iterrows():
        region = base_row["Region"]
        product = base_row["Product"]

        previous_required = num(base_row["Current SE"])
        previous_available = num(base_row["Current SE"])

        for year in YEARS:
            growth_table = growth_inputs.get(region, pd.DataFrame())

            if "Product" in growth_table.columns:
                product_growth_row = growth_table[growth_table["Product"] == product]
            else:
                product_growth_row = pd.DataFrame()

            if product_growth_row.empty:
                bau_growth = 0.0
                dc_growth = 0.0
            else:
                bau_growth = num(product_growth_row["BAU %"].iloc[0]) if "BAU %" in product_growth_row.columns else 0.0
                dc_growth = num(product_growth_row["DC %"].iloc[0]) if "DC %" in product_growth_row.columns else 0.0

            attrition = num(attrition_inputs.get(year, 0))

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
                    "Product Display": PRODUCT_NAME.get(product, product),
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
    selected = detailed[detailed["Year"].isin(selected_years)].copy()

    yearwise = selected.groupby("Year", as_index=False).agg(
        {
            "Available SE After Attrition": "sum",
            "BAU Required SE": "sum",
            "DC Incremental SE": "sum",
            "Combined Required SE": "sum",
            "Hiring Need": "sum",
            "Closing Available SE": "sum",
        }
    )

    value_cols = [column for column in yearwise.columns if column != "Year"]
    yearwise[value_cols] = yearwise[value_cols].round(0).astype(int)

    product_priority = selected.groupby("Product Display", as_index=False).agg(
        {
            "Combined Required SE": "sum",
            "Hiring Need": "sum",
        }
    )

    product_priority = product_priority.rename(
        columns={
            "Product Display": "Product",
            "Combined Required SE": "Selected Years Required SE",
            "Hiring Need": "Selected Years Hiring SE",
        }
    )

    product_priority[["Selected Years Required SE", "Selected Years Hiring SE"]] = product_priority[
        ["Selected Years Required SE", "Selected Years Hiring SE"]
    ].round(0).astype(int)

    product_priority = product_priority.sort_values("Selected Years Required SE", ascending=False)

    regional_priority = selected.groupby("Region", as_index=False).agg(
        {
            "Combined Required SE": "sum",
            "Hiring Need": "sum",
        }
    )

    regional_priority = regional_priority.rename(
        columns={
            "Combined Required SE": "Selected Years Required SE",
            "Hiring Need": "Selected Years Hiring SE",
        }
    )

    regional_priority[["Selected Years Required SE", "Selected Years Hiring SE"]] = regional_priority[
        ["Selected Years Required SE", "Selected Years Hiring SE"]
    ].round(0).astype(int)

    regional_priority = regional_priority.sort_values("Selected Years Required SE", ascending=False)

    bu = selected.groupby(["Region", "Product Display"], as_index=False).agg(
        {
            "Combined Required SE": "sum",
            "Hiring Need": "sum",
        }
    )

    bu = bu.rename(
        columns={
            "Product Display": "Product",
            "Combined Required SE": "Selected Years Required SE",
            "Hiring Need": "Selected Years Hiring SE",
        }
    )

    bu[["Selected Years Required SE", "Selected Years Hiring SE"]] = bu[
        ["Selected Years Required SE", "Selected Years Hiring SE"]
    ].round(0).astype(int)

    bu = bu.sort_values(["Region", "Selected Years Required SE"], ascending=[True, False])

    growth_factor_rows = []

    for region, growth_df in growth_inputs.items():
        for _, growth_row in growth_df.iterrows():
            product = growth_row.get("Product", "")

            growth_factor_rows.append(
                {
                    "Region": region,
                    "Product": PRODUCT_NAME.get(product, product),
                    "BAU Growth %": num(growth_row.get("BAU %", 0)),
                    "DC Growth %": num(growth_row.get("DC %", 0)),
                }
            )

    growth_factors = pd.DataFrame(growth_factor_rows)

    current_base = whole(base_df["Current SE"].sum())
    final_year = max(selected_years)
    final_row = yearwise[yearwise["Year"] == final_year].iloc[0]

    final_required = whole(final_row["Combined Required SE"])
    available_final = whole(final_row["Available SE After Attrition"])
    total_hiring = whole(yearwise["Hiring Need"].sum())

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

    summary = {
        "current_base_se": current_base,
        "selected_years": selected_years,
        "final_year": final_year,
        "final_year_required_se": final_required,
        "available_after_attrition_final_year": available_final,
        "total_hiring_need": total_hiring,
        "highest_annual_hiring_year": whole(high_row["Year"]),
        "highest_annual_hiring_need": whole(high_row["Hiring Need"]),
        "final_year_growth_vs_current_base_pct": growth_pct,
        "total_hiring_intensity_pct": hiring_intensity,
        "interpretation": interpretation,
    }

    return summary, detailed, yearwise, product_priority, regional_priority, bu, growth_factors


with st.sidebar:
    st.markdown(
        '<div class="title" style="font-size:20px">Planning Assumptions</div><div class="sub">Upload base CSV, edit assumptions, then click Apply Assumptions.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Upload Base SE CSV")

    uploaded = st.file_uploader(
        "Upload current SE base CSV",
        type=["csv"],
        help="Required columns: Region, Product, Current SE",
    )

    active_base, upload_message = load_csv(uploaded)

    if uploaded is None:
        st.info(upload_message)
    elif upload_message.startswith("Using uploaded"):
        st.success(upload_message)
    else:
        st.warning(upload_message)

    with st.expander("CSV Format Example"):
        st.code(
            "Region,Product,Current SE\nNorth,UPS,35\nNorth,Cooling,18\nWest,UPS,47\nSouth,UPS,42\nEast,UPS,22",
            language="csv",
        )

    st.markdown("#### Forecast Years")

    selected_years = st.multiselect(
        "Select forecast years",
        YEARS,
        default=YEARS,
    )

    if not selected_years:
        selected_years = YEARS

    selected_years = sorted(selected_years)

    st.markdown("#### Attrition Assumptions")

    attrition_inputs = {}

    for year in YEARS:
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
        st.markdown(
            f'<div class="region {REGION_STYLE[region]}"><b>{region} Growth</b><br><span style="font-size:12px;color:#697386">Product-wise BAU and DC growth assumptions</span></div>',
            unsafe_allow_html=True,
        )

        growth_inputs[region] = st.data_editor(
            growth_template(region),
            hide_index=True,
            use_container_width=True,
            key=f"growth_{region}",
        )

    st.button("Apply Assumptions")


(
    summary,
    detailed_df,
    yearwise_df,
    product_priority_df,
    regional_priority_df,
    bu_df,
    growth_factors_df,
) = run_model(
    active_base,
    growth_inputs,
    attrition_inputs,
    selected_years,
)


tab_summary, tab_input, tab_full, tab_bu, tab_yearly, tab_growth, tab_download = st.tabs(
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


with tab_summary:
    st.markdown(
        '<div class="title">Executive Summary - Leadership View</div><div class="sub">Headcount-based workforce forecast using uploaded or default base SE data.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'''
        <div class="kpis">
            <div class="kpi blue">
                <div class="kpi-label">Current Base SE</div>
                <div class="kpi-value">{summary["current_base_se"]}</div>
            </div>
            <div class="kpi purple">
                <div class="kpi-label">{summary["final_year"]} Required SE</div>
                <div class="kpi-value">{summary["final_year_required_se"]}</div>
            </div>
            <div class="kpi orange">
                <div class="kpi-label">Total Hiring Need</div>
                <div class="kpi-value">{summary["total_hiring_need"]}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        f'''
        <div class="callout">
            <div style="font-size:24px;font-weight:850">Leadership Readout</div>
            <ul>
                <li>Forecast period selected: <span class="hi">{", ".join(map(str, summary["selected_years"]))}</span>.</li>
                <li>Current installed service engineering base: <span class="hi">{summary["current_base_se"]} SE</span>.</li>
                <li>Projected requirement by <span class="hi">{summary["final_year"]}</span>: <span class="hi">{summary["final_year_required_se"]} SE</span>.</li>
                <li>Available SE after attrition before hiring by <span class="hi">{summary["final_year"]}</span>: <span class="hi">{summary["available_after_attrition_final_year"]} SE</span>.</li>
                <li>Total additional hiring required across selected years: <span class="warn">{summary["total_hiring_need"]} SE</span>.</li>
                <li>Highest annual hiring requirement is in <span class="warn">{summary["highest_annual_hiring_year"]}</span> with <span class="warn">{summary["highest_annual_hiring_need"]} SE</span>.</li>
                <li>Leadership interpretation: <span class="warn">{summary["interpretation"]}</span>.</li>
                <li>Strategic implication: final-year requirement is approximately <span class="hi">{summary["final_year_growth_vs_current_base_pct"]}%</span> movement versus current base, and hiring intensity is approximately <span class="hi">{summary["total_hiring_intensity_pct"]}%</span>.</li>
                <li>Recommended focus: <span class="ok">hiring phasing, onboarding bandwidth, delivery readiness, utilization balance, and regional deployment capacity.</span></li>
            </ul>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="hdr">Year-wise Workforce Outlook</div>', unsafe_allow_html=True)

    st.dataframe(
        yearwise_df,
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns([1.35, 1])

    with col1:
        st.markdown('<div class="hdr">Product Prioritization</div>', unsafe_allow_html=True)

        st.dataframe(
            product_priority_df,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown('<div class="hdr">Regional Prioritization</div>', unsafe_allow_html=True)

        st.dataframe(
            regional_priority_df,
            use_container_width=True,
            hide_index=True,
        )


with tab_input:
    st.markdown('<div class="hdr">Input Data</div>', unsafe_allow_html=True)

    st.markdown("#### Active Base SE Data")

    st.dataframe(
        active_base,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Selected Forecast Years")
    st.write(selected_years)

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


with tab_full:
    st.markdown('<div class="hdr">Full Results</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="strip">Full region-product-year forecast output.</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        detailed_df,
        use_container_width=True,
        hide_index=True,
    )


with tab_bu:
    st.markdown('<div class="hdr">BU Requirement Comparison</div>', unsafe_allow_html=True)

    st.dataframe(
        bu_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Pivot View: Region x Product")

    pivot = bu_df.pivot_table(
        index="Region",
        columns="Product",
        values="Selected Years Required SE",
        aggfunc="sum",
        fill_value=0,
    )

    st.dataframe(
        pivot,
        use_container_width=True,
    )


with tab_yearly:
    st.markdown('<div class="hdr">Yearly Tables</div>', unsafe_allow_html=True)

    for year in YEARS:
        st.markdown(f"#### {year}")

        st.dataframe(
            detailed_df[detailed_df["Year"] == year].copy(),
            use_container_width=True,
            hide_index=True,
        )


with tab_growth:
    st.markdown('<div class="hdr">Growth Factors</div>', unsafe_allow_html=True)

    st.dataframe(
        growth_factors_df,
        use_container_width=True,
        hide_index=True,
    )


with tab_download:
    st.markdown('<div class="hdr">Download</div>', unsafe_allow_html=True)

    sheets = {
        "Executive Summary": pd.DataFrame([summary]),
        "Yearwise Outlook": yearwise_df,
        "Product Priority": product_priority_df,
        "Regional Priority": regional_priority_df,
        "BU Comparison": bu_df,
        "Full Results": detailed_df,
        "Growth Factors": growth_factors_df,
        "Input Base SE": active_base,
    }

    st.download_button(
        "Download Workforce Forecast Excel",
        data=to_excel(sheets),
        file_name="v17_headcount_based_forecast_leadership_view.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.write(list(sheets.keys()))
