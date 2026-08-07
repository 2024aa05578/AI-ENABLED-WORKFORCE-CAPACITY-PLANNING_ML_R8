# ============================================================
# v17_headcount_based_forecast
# Modification: Remove VP View, keep Leadership View only
# Adds colorful left pane and colorful Leadership callout
# ============================================================

import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# Page Styling
# ------------------------------------------------------------
st.markdown(
    """
    <style>
        /* App background */
        .stApp {
            background-color: #ffffff;
        }

        /* Left panel / sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f2f6ff 0%, #eef7f2 100%);
            border-right: 1px solid #d7deea;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {
            color: #263142;
        }

        /* Sidebar card blocks */
        .left-pane-card {
            background: #ffffff;
            border: 1px solid #d8e1ef;
            border-left: 6px solid #4f7cff;
            border-radius: 12px;
            padding: 14px 14px 10px 14px;
            margin-bottom: 16px;
            box-shadow: 0 2px 10px rgba(35, 55, 90, 0.06);
        }

        .left-pane-card-north {
            border-left-color: #4f7cff;
        }

        .left-pane-card-west {
            border-left-color: #ff9f43;
        }

        .left-pane-card-south {
            border-left-color: #20c997;
        }

        .left-pane-card-east {
            border-left-color: #a066ff;
        }

        .left-pane-title {
            font-weight: 700;
            font-size: 15px;
            margin-bottom: 8px;
            color: #222b45;
        }

        .left-pane-subtitle {
            font-size: 12px;
            color: #5d6678;
            margin-bottom: 10px;
        }

        /* Main title */
        .leadership-title {
            font-size: 30px;
            font-weight: 800;
            color: #252a34;
            margin-bottom: 18px;
        }

        /* KPI cards */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 28px;
        }

        .kpi-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px 22px;
            box-shadow: 0 4px 18px rgba(30, 45, 90, 0.08);
            border: 1px solid #edf0f7;
        }

        .kpi-card-blue {
            border-top: 6px solid #4f7cff;
            background: linear-gradient(180deg, #f7f9ff 0%, #ffffff 100%);
        }

        .kpi-card-purple {
            border-top: 6px solid #8e5cff;
            background: linear-gradient(180deg, #faf7ff 0%, #ffffff 100%);
        }

        .kpi-card-orange {
            border-top: 6px solid #ff9f43;
            background: linear-gradient(180deg, #fff8ef 0%, #ffffff 100%);
        }

        .kpi-label {
            font-size: 13px;
            color: #687386;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 34px;
            color: #242936;
            font-weight: 800;
            line-height: 1.1;
        }

        /* Leadership callout */
        .leadership-callout {
            background: linear-gradient(135deg, #eef4ff 0%, #f8f0ff 45%, #fff8ec 100%);
            border: 1px solid #dfe7ff;
            border-left: 8px solid #4f7cff;
            border-radius: 18px;
            padding: 22px 26px;
            margin: 14px 0 28px 0;
            box-shadow: 0 5px 22px rgba(41, 65, 120, 0.10);
        }

        .leadership-callout-title {
            font-size: 23px;
            font-weight: 800;
            color: #242936;
            margin-bottom: 12px;
        }

        .leadership-callout ul {
            margin-top: 8px;
            margin-bottom: 0;
            padding-left: 22px;
        }

        .leadership-callout li {
            margin-bottom: 9px;
            font-size: 15px;
            color: #303747;
            line-height: 1.55;
        }

        .leadership-highlight {
            font-weight: 800;
            color: #1f5eff;
        }

        .leadership-warning {
            font-weight: 800;
            color: #d97706;
        }

        .section-header {
            font-size: 24px;
            font-weight: 800;
            color: #2c3140;
            margin-top: 26px;
            margin-bottom: 12px;
        }

        /* Table spacing */
        div[data-testid="stDataFrame"] {
            margin-bottom: 24px;
        }

        /* Make Streamlit tabs cleaner */
        button[data-baseweb="tab"] {
            font-size: 14px;
            font-weight: 600;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ff4b4b;
        }

        /* Apply button */
        div.stButton > button {
            background: linear-gradient(90deg, #4f7cff 0%, #20c997 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            padding: 0.55rem 1rem;
        }

        div.stButton > button:hover {
            background: linear-gradient(90deg, #3d66d6 0%, #17a884 100%);
            color: white;
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# Helper: Colorful Left Pane Cards
# ------------------------------------------------------------
def render_left_pane_region_card(region_name, css_class="left-pane-card"):
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="left-pane-title">{region_name} Growth</div>
            <div class="left-pane-subtitle">Region and product-wise growth assumptions</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Sidebar / Left Pane
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### Planning Assumptions")
    st.caption("Edit assumptions and click **Apply Assumptions**.")

    st.markdown("#### 2027 Region and Product Wise Growth")

    # Example region blocks.
    # Keep your existing input widgets/data editor inside or after each card as per current v17 logic.

    render_left_pane_region_card("North", "left-pane-card left-pane-card-north")
    north_growth_df = st.data_editor(
        pd.DataFrame({
            "Product": ["UPS", "Cooling", "Power Prod", "Power Sys"],
            "BAU ^%": [10, 10, 10, 10],
            "DC ^%": ["", "", "", ""]
        }),
        hide_index=True,
        use_container_width=True,
        key="north_growth_editor"
    )

    render_left_pane_region_card("West", "left-pane-card left-pane-card-west")
    west_growth_df = st.data_editor(
        pd.DataFrame({
            "Product": ["UPS", "Cooling", "Power Prod", "Power Sys"],
            "BAU ^%": [10, 10, 10, 10],
            "DC ^%": [4, 4, 2, 2]
        }),
        hide_index=True,
        use_container_width=True,
        key="west_growth_editor"
    )

    render_left_pane_region_card("South", "left-pane-card left-pane-card-south")
    south_growth_df = st.data_editor(
        pd.DataFrame({
            "Product": ["UPS", "Cooling", "Power Prod", "Power Sys"],
            "BAU ^%": [10, 10, 10, 10],
            "DC ^%": [2, 2, "", ""]
        }),
        hide_index=True,
        use_container_width=True,
        key="south_growth_editor"
    )

    render_left_pane_region_card("East", "left-pane-card left-pane-card-east")
    east_growth_df = st.data_editor(
        pd.DataFrame({
            "Product": ["UPS", "Cooling", "Power Prod", "Power Sys"],
            "BAU ^%": [10, 10, 10, 10],
            "DC ^%": ["", "", "", ""]
        }),
        hide_index=True,
        use_container_width=True,
        key="east_growth_editor"
    )

    apply_assumptions = st.button("Apply Assumptions")


# ------------------------------------------------------------
# Existing Tabs
# Rename Executive Summary behavior to Leadership only
# ------------------------------------------------------------
tabs = st.tabs([
    "Executive Summary",
    "Input Data",
    "Full Results",
    "BU Requirement Comparison",
    "Yearly Tables",
    "Growth Factors",
    "Download"
])

with tabs# --------------------------------------------------------
    # IMPORTANT:
    # Replace these sample values with your existing calculated
    # variables from v17_headcount_based_forecast.
    # --------------------------------------------------------

    selected_years = [2027, 2028, 2029]

    current_base_se = 281
    final_year = 2029
    final_year_required_se = 771
    available_se_after_attrition_final_year = 483
    total_hiring_need = 557
    highest_annual_hiring_year = 2029
    highest_annual_hiring_need = 297

    final_year_growth_vs_current_base_pct = round(
        ((final_year_required_se - current_base_se) / current_base_se) * 100
    )

    total_hiring_intensity_pct = round(
        (total_hiring_need / current_base_se) * 100
    )

    # --------------------------------------------------------
    # Title: VP removed, Leadership retained
    # --------------------------------------------------------
    st.markdown(
        """
        <div class="leadership-title">
            Executive Summary - Leadership View
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Colorful KPI Callout Cards
    # --------------------------------------------------------
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card kpi-card-blue">
                <div class="kpi-label">Current Base SE</div>
                <div class="kpi-value">{current_base_se}</div>
            </div>
            <div class="kpi-card kpi-card-purple">
                <div class="kpi-label">{final_year} Required SE</div>
                <div class="kpi-value">{final_year_required_se}</div>
            </div>
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-label">Total Hiring Need</div>
                <div class="kpi-value">{total_hiring_need}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # --------------------------------------------------------
    # Leadership Readout as Bullet Points
    # --------------------------------------------------------
    st.markdown(
        f"""
        <div class="leadership-callout">
            <div class="leadership-callout-title">
                Leadership Readout
            </div>
            <ul>
                <li>
                    Forecast period selected:
                    <span class="leadership-highlight">{", ".join(map(str, selected_years))}</span>.
                </li>
                <li>
                    Current installed service engineering base:
                    <span class="leadership-highlight">{current_base_se} SE</span>.
                </li>
                <li>
                    Projected requirement by
                    <span class="leadership-highlight">{final_year}</span>:
                    <span class="leadership-highlight">{final_year_required_se} SE</span>.
                </li>
                <li>
                    Available SE after attrition before hiring by
                    <span class="leadership-highlight">{final_year}</span>:
                    <span class="leadership-highlight">{available_se_after_attrition_final_year} SE</span>.
                </li>
                <li>
                    Total additional hiring required across selected years:
                    <span class="leadership-warning">{total_hiring_need} SE</span>.
                </li>
                <li>
                    Highest annual hiring requirement is in
                    <span class="leadership-warning">{highest_annual_hiring_year}</span>
                    with
                    <span class="leadership-warning">{highest_annual_hiring_need} SE</span>.
                </li>
                <li>
                    Leadership interpretation:
                    <span class="leadership-warning">High expansion requirement</span>,
                    requiring active planning on hiring phasing, onboarding bandwidth,
                    delivery readiness, and regional deployment capacity.
                </li>
                <li>
                    Strategic implication:
                    Final-year requirement represents approximately
                    <span class="leadership-highlight">{final_year_growth_vs_current_base_pct}%</span>
                    movement versus current base, while selected-year hiring intensity is approximately
                    <span class="leadership-highlight">{total_hiring_intensity_pct}%</span>
                    of the current base.
                </li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Year-wise Workforce Outlook
    # Replace this sample dataframe with existing v17 dataframe
    # if already available.
    # --------------------------------------------------------
    st.markdown(
        """
        <div class="section-header">
            Year-wise Workforce Outlook
        </div>
        """,
        unsafe_allow_html=True
    )

    yearwise_workforce_outlook_df = pd.DataFrame({
        "Year": [2027, 2028, 2029],
        "Available SE After Attrition": [267, 348, 483],
        "BAU Required SE": [309, 406, 570],
        "DC Incremental SE": [48, 91, 201],
        "Combined Required SE": [357, 497, 771],
        "Hiring Need": [90, 149, 297]
    })

    st.dataframe(
        yearwise_workforce_outlook_df,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # Product Prioritization and Regional Prioritization
    # Replace sample dataframes with existing v17 model outputs
    # --------------------------------------------------------
    col1, col2 = st.columns([1.35, 1])

    with col1:
        st.markdown(
            """
            <div class="section-header">
                Product Prioritization
            </div>
            """,
            unsafe_allow_html=True
        )

        product_prioritization_df = pd.DataFrame({
            "Product": ["UPS", "Cooling", "Power System", "Power Product"],
            "Selected Years Required SE": [875, 278, 322, 186],
            "Selected Years Hiring SE": [319, 107, 84, 47]
        })

        st.dataframe(
            product_prioritization_df,
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown(
            """
            <div class="section-header">
                Regional Prioritization
            </div>
            """,
            unsafe_allow_html=True
        )

        regional_prioritization_df = pd.DataFrame({
            "Region": ["West", "South", "North", "East"],
            "Selected Years Required SE": [624, 471, 334, 232],
            "Selected Years Hiring SE": [212, 168, 103, 74]
        })

        st.dataframe(
            regional_prioritization_df,
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# Other tabs retained as-is
# Plug your existing v17 code blocks below
# ------------------------------------------------------------

with tabsst.markdown("### Input Data")
    st.info("Retain existing v17 Input Data code here.")

with tabsst.markdown("### Full Results")
    st.info("Retain existing v17 Full Results code here.")

with tabsst.markdown("### BU Requirement Comparison")
    st.info("Retain existing v17 BU Requirement Comparison code here.")

with tabsst.markdown("### Yearly Tables")
    st.info("Retain existing v17 Yearly Tables code here.")

with tabsst.markdown("### Growth Factors")
    st.info("Retain existing v17 Growth Factors code here.")

with tabsst.markdown("### Download")
    st.info("Retain existing v17 Download code here.")
