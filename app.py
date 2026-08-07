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


def build_growth_df(region):
    return pd.DataFrame(
        {
            "Product": PRODUCTS,
            "BAU ^%": [DEFAULT_BAU[region][product] for product in PRODUCTS],
            "DC ^%": [DEFAULT_DC[region][product] for product in PRODUCTS],
        }
    )


def region_card(region):
    st.markdown(
        f'<div class="region-card {STYLE_MAP[region]}"><div class="region-title">{region} Growth</div><div class="region-sub">Product-wise BAU and DC growth assumptions</div></div>',
        unsafe_allow_html=True,
    )


def make_excel(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


def load_base_se_from_csv(uploaded_file):
    if uploaded_file is None:
        return DEFAULT_BASE_SE.copy(), "Using default base SE data."

    try:
        uploaded_df = pd.read_csv(uploaded_file)

        required_columns = ["Region", "Product", "Current SE"]
        missing = [column for column in required_columns if column not in uploaded_df.columns]

        if missing:
            return DEFAULT_BASE_SE.copy(), "Upload ignored. Missing required columns: " + ", ".join(missing)

        uploaded_df = uploaded_df[required_columns].copy()
        uploaded_df["Region"] = uploaded_df["Region"].astype(str).str.strip()
        uploaded_df["Product"] = uploaded_df["Product"].astype(str).str.strip()
        uploaded_df["Current SE"] = pd.to_numeric(uploaded_df["Current SE"], errors="coerce").fillna(0)

        valid_rows = uploaded_df["Region"].isin(REGIONS) & uploaded_df["Product"].isin(PRODUCTS)
        uploaded_df = uploaded_df[valid_rows].copy()

        if uploaded_df.empty:
            return DEFAULT_BASE_SE.copy(), "Upload ignored. No valid Region/Product rows found."

        uploaded_df = uploaded_df.groupby(["Region", "Product"], as_index=False).agg({"Current SE": "sum"})

        return uploaded_df, "Using uploaded CSV base SE data."

    except Exception as error:
        return DEFAULT_BASE_SE.copy(), f"Upload failed. Using default base SE data. Error: {error}"


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

        return summary, detailed, yearwise, product_priority, regional_priority, bu_comparison, growth_factors

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
                "
