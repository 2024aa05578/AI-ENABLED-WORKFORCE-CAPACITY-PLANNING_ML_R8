import pandas as pd
import numpy as np


# ------------------------------------------------------------
# Default input tables
# ------------------------------------------------------------
def get_default_base_workforce():
    return pd.DataFrame(
        {
            "Role": [
                "Project Manager",
                "Service Delivery Manager",
                "Technical Lead",
                "Engineer",
                "Support Executive"
            ],
            "Current HC": [
                12,
                18,
                35,
                120,
                60
            ],
            "Current Productivity": [
                1.00,
                1.00,
                1.00,
                1.00,
                1.00
            ]
        }
    )


def get_default_bau_growth_assumptions():
    return pd.DataFrame(
        {
            "Year": [
                "Year 1",
                "Year 2",
                "Year 3"
            ],
            "BAU Growth %": [
                8.0,
                7.0,
                6.0
            ]
        }
    )


def get_default_dc_growth_assumptions():
    return pd.DataFrame(
        {
            "Year": [
                "Year 1",
                "Year 2",
                "Year 3"
            ],
            "DC Growth %": [
                5.0,
                5.0,
                4.0
            ]
        }
    )


def get_default_attrition_assumptions():
    return pd.DataFrame(
        {
            "Year": [
                "Year 1",
                "Year 2",
                "Year 3"
            ],
            "Attrition %": [
                10.0,
                9.0,
                8.0
            ]
        }
    )


def get_default_productivity_assumptions():
    return pd.DataFrame(
        {
            "Year": [
                "Year 1",
                "Year 2",
                "Year 3"
            ],
            "Productivity Improvement %": [
                3.0,
                4.0,
                5.0
            ]
        }
    )


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
def validate_assumptions(
    base_df,
    bau_df,
    dc_df,
    attrition_df,
    productivity_df
):
    required_years = [
        "Year 1",
        "Year 2",
        "Year 3"
    ]

    if base_df.empty:
        raise ValueError("Base workforce table cannot be empty.")

    required_base_columns = [
        "Role",
        "Current HC",
        "Current Productivity"
    ]

    for column in required_base_columns:
        if column not in base_df.columns:
            raise ValueError(f"Base workforce must contain '{column}' column.")

    assumption_tables = [
        (
            bau_df,
            "BAU Growth",
            "BAU Growth %"
        ),
        (
            dc_df,
            "DC Growth",
            "DC Growth %"
        ),
        (
            attrition_df,
            "Attrition",
            "Attrition %"
        ),
        (
            productivity_df,
            "Productivity",
            "Productivity Improvement %"
        )
    ]

    for df, table_name, value_column in assumption_tables:
        if df.empty:
            raise ValueError(f"{table_name} table cannot be empty.")

        if "Year" not in df.columns:
            raise ValueError(f"{table_name} table must contain 'Year' column.")

        if value_column not in df.columns:
            raise ValueError(f"{table_name} table must contain '{value_column}' column.")

        available_years = df["Year"].tolist()

        for year in required_years:
            if year not in available_years:
                raise ValueError(f"{table_name} table must contain {year}.")


# ------------------------------------------------------------
# Projection calculation
# ------------------------------------------------------------
def calculate_projection(
    base_df,
    bau_df,
    dc_df,
    attrition_df,
    productivity_df
):
    validate_assumptions(
        base_df,
        bau_df,
        dc_df,
        attrition_df,
        productivity_df
    )

    projection_rows = []

    current_hc_by_role = base_df.set_index("Role")["Current HC"].to_dict()
    current_productivity_by_role = base_df.set_index("Role")["Current Productivity"].to_dict()

    years = [
        "Year 1",
        "Year 2",
        "Year 3"
    ]

    for year in years:
        bau_growth = float(
            bau_df.loc[
                bau_df["Year"] == year,
                "BAU Growth %"
            ].iloc[0]
        ) / 100

        dc_growth = float(
            dc_df.loc[
                dc_df["Year"] == year,
                "DC Growth %"
            ].iloc[0]
        ) / 100

        attrition = float(
            attrition_df.loc[
                attrition_df["Year"] == year,
                "Attrition %"
            ].iloc[0]
        ) / 100

        productivity_improvement = float(
            productivity_df.loc[
                productivity_df["Year"] == year,
                "Productivity Improvement %"
            ].iloc[0]
        ) / 100

        for role in base_df["Role"]:
            opening_hc = float(current_hc_by_role[role])
            current_productivity = float(current_productivity_by_role[role])

            total_growth = bau_growth + dc_growth

            demand_hc_before_productivity = opening_hc * (
                1 + total_growth
            )

            improved_productivity = current_productivity * (
                1 + productivity_improvement
            )

            if improved_productivity == 0:
                required_hc_after_productivity = demand_hc_before_productivity
            else:
                required_hc_after_productivity = (
                    demand_hc_before_productivity / improved_productivity
                )

            attrition_backfill = opening_hc * attrition

            gross_hiring_required = (
                required_hc_after_productivity
                + attrition_backfill
                - opening_hc
            )

            gross_hiring_required = max(
                gross_hiring_required,
                0
            )

            closing_hc = opening_hc + gross_hiring_required

            projection_rows.append(
                {
                    "Year": year,
                    "Role": role,
                    "Opening HC": round(opening_hc, 2),
                    "BAU Growth %": round(bau_growth * 100, 1),
                    "DC Growth %": round(dc_growth * 100, 1),
                    "Total Growth %": round(total_growth * 100, 1),
                    "Attrition %": round(attrition * 100, 1),
                    "Productivity Improvement %": round(productivity_improvement * 100, 1),
                    "Demand HC Before Productivity": round(demand_hc_before_productivity, 2),
                    "Required HC After Productivity": round(required_hc_after_productivity, 2),
                    "Attrition Backfill": round(attrition_backfill, 2),
                    "Gross Hiring Required": round(gross_hiring_required, 2),
                    "Closing HC": round(closing_hc, 2)
                }
            )

            current_hc_by_role[role] = closing_hc
            current_productivity_by_role[role] = improved_productivity

    projection_df = pd.DataFrame(projection_rows)

    return projection_df


# ------------------------------------------------------------
# Summary creation
# ------------------------------------------------------------
def create_summary(projection_df):
    summary_df = (
        projection_df.groupby(
            "Year",
            as_index=False
        )
        .agg(
            {
                "Opening HC": "sum",
                "Required HC After Productivity": "sum",
                "Attrition Backfill": "sum",
                "Gross Hiring Required": "sum",
                "Closing HC": "sum"
            }
        )
    )

    numeric_cols = summary_df.select_dtypes(
        include=[
            np.number
        ]
    ).columns

    summary_df[numeric_cols] = summary_df[numeric_cols].round(2)

    return summary_df


# ------------------------------------------------------------
# Split projection into required tabs
# ------------------------------------------------------------
def split_projection_tabs(
    projection_df,
    summary_df
):
    next_year_df = projection_df[
        projection_df["Year"] == "Year 1"
    ].copy()

    remaining_years_df = projection_df[
        projection_df["Year"].isin(
            [
                "Year 2",
                "Year 3"
            ]
        )
    ].copy()

    next_year_summary = summary_df[
        summary_df["Year"] == "Year 1"
    ].copy()

    remaining_years_summary = summary_df[
        summary_df["Year"].isin(
            [
                "Year 2",
                "Year 3"
            ]
        )
    ].copy()

    return (
        next_year_df,
        remaining_years_df,
        next_year_summary,
        remaining_years_summary
    )
