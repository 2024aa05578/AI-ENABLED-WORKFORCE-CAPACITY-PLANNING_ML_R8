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
    # Three-year workforce forecast for 2027, 2028 and 2029.
    # 2027 BAU/DC growth comes from region-product growth assumptions.
    # 2028 growth = 2027 growth x region-level 2028 factor.
    # 2029 growth = 2028 growth x region-level 2029 factor.
    # Available engineers roll forward from previous year's required engineers after attrition.

    if df is None or df.empty:
        return pd.DataFrame()

    monthly_capacity = productive_hours * working_days * (target_utilization / 100.0)

    if monthly_capacity <= 0:
        raise ValueError("Monthly capacity must be greater than zero. Check productivity assumptions.")

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

        previous_required_engineers = current_se_2026
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

            available_engineers = previous_required_engineers * (1 - attrition_pct / 100.0)

            bau_hours = base_total_hours * (1 + bau_growth_pct / 100.0)
            dc_incremental_hours = base_total_hours * (dc_growth_pct / 100.0)
            combined_hours = bau_hours + dc_incremental_hours

            bau_required_engineers = bau_hours / monthly_capacity
            dc_incremental_engineers = dc_incremental_hours / monthly_capacity
            combined_required_engineers = combined_hours / monthly_capacity

            combined_additional_required = max(
                math.ceil(combined_required_engineers - available_engineers),
                0,
            )

            results.append(
                {
                    "Region": region,
                    "Product": product,
                    "Year": year,
                    "Base Total Hours": round(base_total_hours, 2),
                    "BAU Growth %": round(bau_growth_pct, 2),
                    "DC Growth %": round(dc_growth_pct, 2),
                    "Current Engineers Base": round(previous_required_engineers, 2),
                    "Attrition %": round(attrition_pct, 2),
                    "Available Engineers": round(available_engineers, 2),
                    "BAU Required Engineers": round(bau_required_engineers, 2),
                    "DC Incremental Engineers": round(dc_incremental_engineers, 2),
                    "Combined Required Engineers": round(combined_required_engineers, 2),
                    "Combined Additional Required": int(combined_additional_required),
                }
            )

            previous_required_engineers = combined_required_engineers
            previous_bau_growth = bau_growth_pct
            previous_dc_growth = dc_growth_pct

    return pd.DataFrame(results)
