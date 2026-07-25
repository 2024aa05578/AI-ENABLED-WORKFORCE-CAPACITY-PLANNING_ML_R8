import math
import pandas as pd

FORECAST_YEARS = [2027, 2028, 2029]


def _safe_number(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def calculate_workforce(
    df,
    growth_parameters,
    growth_factors,
    attrition_parameters,
    productive_hours,
    working_days,
    target_utilization,
):
    """
    Rolling three-year workforce forecast for 2027, 2028 and 2029.

    Logic:
    - 2027 BAU/DC growth comes from region-product growth assumptions.
    - 2028 BAU/DC growth = 2027 growth x region-level 2028 factor.
    - 2029 BAU/DC growth = 2028 growth x region-level 2029 factor.
    - Workload rolls forward year by year; 2028 is calculated on 2027 workload,
      and 2029 is calculated on 2028 workload.
    - Engineer availability rolls forward using previous year ending headcount
      after hiring and then applying attrition.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    monthly_capacity = productive_hours * working_days * (target_utilization / 100.0)

    if monthly_capacity <= 0:
        raise ValueError(
            "Monthly capacity must be greater than zero. Check productivity assumptions."
        )

    grouped = df.groupby(["Region", "Product"], as_index=False).agg(
        Current_SE=("Current_SE", "sum"),
        Breakdown_WO=("Breakdown_WO", "sum"),
        Breakdown_Hrs=("Breakdown_Hrs", "sum"),
        PM_WO=("PM_WO", "sum"),
        PM_Hrs=("PM_Hrs", "sum"),
        Startup_WO=("Startup_WO", "sum"),
        Startup_Hrs=("Startup_Hrs", "sum"),
    )

    results = []

    for _, row in grouped.iterrows():
        region = row["Region"]
        product = row["Product"]

        current_se_2026 = _safe_number(row["Current_SE"])
        attrition_pct = _safe_number(attrition_parameters.get(product, 0.0))

        base_bau_growth = _safe_number(
            growth_parameters[region][product].get("BAU", 0.0)
        )

        base_dc_growth = _safe_number(
            growth_parameters[region][product].get("DC", 0.0)
        )

        base_total_hours = (
            _safe_number(row["Breakdown_Hrs"])
            + _safe_number(row["PM_Hrs"])
            + _safe_number(row["Startup_Hrs"])
        )

        previous_total_hours = base_total_hours
        previous_ending_engineers = current_se_2026
        previous_bau_growth = base_bau_growth
        previous_dc_growth = base_dc_growth

        for year in FORECAST_YEARS:
            if year == 2027:
                bau_growth_pct = base_bau_growth
                dc_growth_pct = base_dc_growth

            elif year == 2028:
                bau_growth_pct = previous_bau_growth * _safe_number(
                    growth_factors[region].get("2028 BAU Factor", 1.0),
                    1.0,
                )

                dc_growth_pct = previous_dc_growth * _safe_number(
                    growth_factors[region].get("2028 DC Factor", 1.0),
                    1.0,
                )

            else:
                bau_growth_pct = previous_bau_growth * _safe_number(
                    growth_factors[region].get("2029 BAU Factor", 1.0),
                    1.0,
                )

                dc_growth_pct = previous_dc_growth * _safe_number(
                    growth_factors[region].get("2029 DC Factor", 1.0),
                    1.0,
                )

            available_engineers = previous_ending_engineers * (
                1 - attrition_pct / 100.0
            )

            bau_hours = previous_total_hours * (1 + bau_growth_pct / 100.0)
            dc_incremental_hours = previous_total_hours * (dc_growth_pct / 100.0)
            combined_hours = bau_hours + dc_incremental_hours

            bau_required_engineers = bau_hours / monthly_capacity
            dc_incremental_engineers = dc_incremental_hours / monthly_capacity
            combined_required_engineers = combined_hours / monthly_capacity

            combined_additional_required = max(
                math.ceil(combined_required_engineers - available_engineers),
                0,
            )

            ending_engineers = available_engineers + combined_additional_required

            results.append(
                {
                    "Region": region,
                    "Product": product,
                    "Year": year,
                    "Opening Workload Hours": round(previous_total_hours, 2),
                    "BAU Growth %": round(bau_growth_pct, 2),
                    "DC Growth %": round(dc_growth_pct, 2),
                    "BAU Required Hours": round(bau_hours, 2),
                    "DC Incremental Hours": round(dc_incremental_hours, 2),
                    "Combined Required Hours": round(combined_hours, 2),
                    "Opening Engineers": round(previous_ending_engineers, 2),
                    "Attrition %": round(attrition_pct, 2),
                    "Available Engineers": round(available_engineers, 2),
                    "BAU Required Engineers": round(bau_required_engineers, 2),
                    "DC Incremental Engineers": round(dc_incremental_engineers, 2),
                    "Combined Required Engineers": round(
                        combined_required_engineers,
                        2,
                    ),
                    "Combined Additional Required": int(
                        combined_additional_required
                    ),
                    "Ending Engineers After Hiring": round(
                        ending_engineers,
                        2,
                    ),
                }
            )

            previous_total_hours = combined_hours
            previous_ending_engineers = ending_engineers
            previous_bau_growth = bau_growth_pct
            previous_dc_growth = dc_growth_pct

    return pd.DataFrame(results)
