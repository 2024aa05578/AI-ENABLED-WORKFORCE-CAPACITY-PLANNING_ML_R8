import streamlit as st
import pandas as pd
import numpy as np
import workforce_model as wm


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Workforce Planning App",
    page_icon="📊",
    layout="wide"
)


# ------------------------------------------------------------
# Session state initialization
# ------------------------------------------------------------
def initialize_session_state():
    if "base_workforce" not in st.session_state:
        st.session_state.base_workforce = wm.get_default_base_workforce()

    if "bau_growth_assumptions" not in st.session_state:
        st.session_state.bau_growth_assumptions = wm.get_default_bau_growth_assumptions()

    if "dc_growth_assumptions" not in st.session_state:
        st.session_state.dc_growth_assumptions = wm.get_default_dc_growth_assumptions()

    if "attrition_assumptions" not in st.session_state:
        st.session_state.attrition_assumptions = wm.get_default_attrition_assumptions()

    if "productivity_assumptions" not in st.session_state:
        st.session_state.productivity_assumptions = wm.get_default_productivity_assumptions()


initialize_session_state()


# ------------------------------------------------------------
# App title
# ------------------------------------------------------------
st.title("Workforce Planning Projection")
st.caption(
    "Next year is shown in one tab and the remaining two years are shown in another tab."
)


# ------------------------------------------------------------
# Sidebar assumptions
# ------------------------------------------------------------
st.sidebar.header("Assumptions Panel")
st.sidebar.info("Edit assumptions below and click Apply Assumptions to refresh the projection.")


st.sidebar.subheader("Base Workforce")

edited_base_workforce = st.sidebar.data_editor(
    st.session_state.base_workforce,
    use_container_width=True,
    num_rows="dynamic",
    key="edited_base_workforce"
)


st.sidebar.subheader("BAU Growth")

edited_bau_growth = st.sidebar.data_editor(
    st.session_state.bau_growth_assumptions,
    use_container_width=True,
    num_rows="fixed",
    key="edited_bau_growth"
)


st.sidebar.subheader("DC Growth")

edited_dc_growth = st.sidebar.data_editor(
    st.session_state.dc_growth_assumptions,
    use_container_width=True,
    num_rows="fixed",
    key="edited_dc_growth"
)


st.sidebar.subheader("Attrition")

edited_attrition = st.sidebar.data_editor(
    st.session_state.attrition_assumptions,
    use_container_width=True,
    num_rows="fixed",
    key="edited_attrition"
)


st.sidebar.subheader("Workforce Productivity")

edited_productivity = st.sidebar.data_editor(
    st.session_state.productivity_assumptions,
    use_container_width=True,
    num_rows="fixed",
    key="edited_productivity"
)


apply_button = st.sidebar.button(
    "Apply Assumptions",
    type="primary",
    use_container_width=True
)


if apply_button:
    st.session_state.base_workforce = edited_base_workforce.copy()
    st.session_state.bau_growth_assumptions = edited_bau_growth.copy()
    st.session_state.dc_growth_assumptions = edited_dc_growth.copy()
    st.session_state.attrition_assumptions = edited_attrition.copy()
    st.session_state.productivity_assumptions = edited_productivity.copy()

    st.sidebar.success("Assumptions applied successfully.")


# ------------------------------------------------------------
# Projection calculation
# ------------------------------------------------------------
try:
    projection_df = wm.calculate_projection(
        st.session_state.base_workforce,
        st.session_state.bau_growth_assumptions,
        st.session_state.dc_growth_assumptions,
        st.session_state.attrition_assumptions,
        st.session_state.productivity_assumptions
    )

    summary_df = wm.create_summary(projection_df)

    (
        next_year_df,
        remaining_years_df,
        next_year_summary,
        remaining_years_summary
    ) = wm.split_projection_tabs(projection_df, summary_df)

except Exception as error:
    st.error(f"Projection calculation failed: {error}")
    st.stop()


# ------------------------------------------------------------
# KPI section
# ------------------------------------------------------------
total_current_hc = st.session_state.base_workforce["Current HC"].sum()
next_year_hiring = next_year_df["Gross Hiring Required"].sum()
remaining_years_hiring = remaining_years_df["Gross Hiring Required"].sum()
total_three_year_hiring = projection_df["Gross Hiring Required"].sum()


kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)

with kpi_1:
    st.metric(
        label="Current HC",
        value=f"{total_current_hc:,.0f}"
    )

with kpi_2:
    st.metric(
        label="Next Year Hiring",
        value=f"{next_year_hiring:,.0f}"
    )

with kpi_3:
    st.metric(
        label="Remaining 2 Years Hiring",
        value=f"{remaining_years_hiring:,.0f}"
    )

with kpi_4:
    st.metric(
        label="Total 3-Year Hiring",
        value=f"{total_three_year_hiring:,.0f}"
    )


# ------------------------------------------------------------
# Main tabs
# ------------------------------------------------------------
tab_next_year, tab_remaining_years, tab_full_projection = st.tabs(
    [
        "Next Year",
        "Remaining 2 Years",
        "Full 3-Year View"
    ]
)


# ------------------------------------------------------------
# Tab 1: Next Year
# ------------------------------------------------------------
with tab_next_year:
    st.subheader("Next Year Projection")

    st.markdown("### Summary")

    st.dataframe(
        next_year_summary,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Role-wise Detail")

    st.dataframe(
        next_year_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Next Year Hiring by Role")

    next_year_chart_df = next_year_df[
        [
            "Role",
            "Gross Hiring Required"
        ]
    ].copy()

    next_year_chart_df = next_year_chart_df.set_index("Role")

    st.bar_chart(next_year_chart_df)


# ------------------------------------------------------------
# Tab 2: Remaining 2 Years
# ------------------------------------------------------------
with tab_remaining_years:
    st.subheader("Remaining 2 Years Projection")

    st.markdown("### Summary")

    st.dataframe(
        remaining_years_summary,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Role-wise Detail")

    st.dataframe(
        remaining_years_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Hiring by Role and Year")

    pivot_hiring = remaining_years_df.pivot_table(
        index="Role",
        columns="Year",
        values="Gross Hiring Required",
        aggfunc="sum"
    ).fillna(0)

    st.dataframe(
        pivot_hiring.round(2),
        use_container_width=True
    )

    st.bar_chart(pivot_hiring)

    st.markdown("### Closing HC by Role and Year")

    pivot_closing_hc = remaining_years_df.pivot_table(
        index="Role",
        columns="Year",
        values="Closing HC",
        aggfunc="sum"
    ).fillna(0)

    st.dataframe(
        pivot_closing_hc.round(2),
        use_container_width=True
    )


# ------------------------------------------------------------
# Tab 3: Full 3-Year View
# ------------------------------------------------------------
with tab_full_projection:
    st.subheader("Full 3-Year Projection")

    st.markdown("### Year-wise Summary")

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Complete Role-wise Projection")

    st.dataframe(
        projection_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Total Hiring by Year")

    hiring_by_year = projection_df.pivot_table(
        index="Year",
        values="Gross Hiring Required",
        aggfunc="sum"
    )

    st.bar_chart(hiring_by_year)


# ------------------------------------------------------------
# Download section
# ------------------------------------------------------------
st.divider()
st.subheader("Download Output")

projection_csv = projection_df.to_csv(index=False).encode("utf-8")
summary_csv = summary_df.to_csv(index=False).encode("utf-8")

download_col_1, download_col_2 = st.columns(2)

with download_col_1:
    st.download_button(
        label="Download Full Projection CSV",
        data=projection_csv,
        file_name="workforce_projection_3_years.csv",
        mime="text/csv",
        use_container_width=True
    )

with download_col_2:
    st.download_button(
        label="Download Summary CSV",
        data=summary_csv,
        file_name="workforce_projection_summary.csv",
        mime="text/csv",
        use_container_width=True
    )


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.caption(
    "Projection uses BAU growth, DC growth, attrition, and workforce productivity assumptions."
)
