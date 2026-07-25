import math
import pandas as pd

FORECAST_YEARS = [2027, 2028, 2029]
MODEL_VERSION = "v19_workload_capacity_planning"


def _safe_number(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_nested_growth(growth_parameters, region, product, growth_type, default=0.0):
    try:
        return _safe_number(
            growth_parameters.get(region, {}).get(product, {}).get(growth_type, default),
            default,
        )
    except Exception:
        return default


def _safe_growth_factor(growth_factors, region, factor_name, default=1.0):
    try:
        return _safe_number(
            growth_factors.get(region, {}).get(factor_name, default),
            default,
        )
    except Exception:
        return default


def _capacity_status(shortage_surplus):
    if shortage_surplus < 0:
        return "Shortage"
    elif shortage_surplus <= 2:
        return "Tight Capacity"
    else:
        return "Surplus"


def calculate_workforce(
    df,
    growth_parameters,
    growth_factors,
    attrition_parameters,
    productive_hours,
    working_days,
    target_utilization,
    capacity_mode="Monthly",
    planning_buffer_pct=0.0,
):
    """
    Workload-based rolling three-year workforce forecast.

    Logic:
    - Base workload hours = WO volume x handling hours.
    - BAU workload = Breakdown + PM.
    - DC workload = Startup.
    - 2027 growth comes from region-product assumptions.
    - 2028 growth = previous year growth x 2028 regional factor.
    - 2029 growth = previous year growth x 2029 regional factor.
    - Attrition is applied first to opening engineers.
    - Required engineers are calculated from workload / engineer capacity.
    - Planning buffer is applied on required engineers.
    - Additional required = required engineers after buffer - available engineers.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    required_columns = [
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

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    monthly_capacity = (
        _safe_number(productive_hours)
        * _safe_number(working_days)
        * (_safe_number(target_utilization) / 100.0)
    )

    if capacity_mode == "Annual":
        engineer_capacity = monthly_capacity * 12
    else:
        engineer_capacity = monthly_capacity

    if engineer_capacity <= 0:
        raise ValueError(
            "Engineer capacity must be greater than zero. "
            "Check productive hours, working days, utilization, and capacity mode."
        )

    grouped = (
        df.groupby(["Region", "Product"], as_index=False)
        .agg(
            Current_SE=("Current_SE", "sum"),
            Breakdown_WO=("Breakdown_WO", "sum"),
            Breakdown_Hrs=("Breakdown_Hrs", "mean"),
            PM_WO=("PM_WO", "sum"),
            PM_Hrs=("PM_Hrs", "mean"),
            Startup_WO=("Startup_WO", "sum"),
            Startup_Hrs=("Startup_Hrs", "mean"),
        )
    )

    results = []

    for _, row in grouped.iterrows():
        region = row["Region"]
        product = row["Product"]

        opening_engineers = _safe_number(row["Current_SE"])

        attrition_pct = _safe_number(
            attrition_parameters.get(product, 0.0)
            if isinstance(attrition_parameters, dict)
            else 0.0
        )

        base_bau_growth = _safe_nested_growth(
            growth_parameters,
            region,
            product,
            "BAU",
            0.0,
        )

        base_dc_growth = _safe_nested_growth(
            growth_parameters,
            region,
            product,
            "DC",
            0.0,
        )

        breakdown_total_hours = (
            _safe_number(row["Breakdown_WO"])
            * _safe_number(row["Breakdown_Hrs"])
        )

        pm_total_hours = (
            _safe_number(row["PM_WO"])
            * _safe_number(row["PM_Hrs"])
        )

        startup_total_hours = (
            _safe_number(row["Startup_WO"])
            * _safe_number(row["Startup_Hrs"])
        )

        base_bau_hours = breakdown_total_hours + pm_total_hours
        base_dc_hours = startup_total_hours
        base_total_hours = base_bau_hours + base_dc_hours

        previous_bau_growth = base_bau_growth
        previous_dc_growth = base_dc_growth

        for year in FORECAST_YEARS:
            if year == 2027:
                bau_growth_pct = base_bau_growth
                dc_growth_pct = base_dc_growth

            elif year == 2028:
                bau_growth_pct = previous_bau_growth * _safe_growth_factor(
                    growth_factors,
                    region,
                    "2028 BAU Factor",
                    1.0,
                )

                dc_growth_pct = previous_dc_growth * _safe_growth_factor(
                    growth_factors,
                    region,
                    "2028 DC Factor",
                    1.0,
                )

            else:
                bau_growth_pct = previous_bau_growth * _safe_growth_factor(
                    growth_factors,
                    region,
                    "2029 BAU Factor",
                    1.0,
                )

                dc_growth_pct = previous_dc_growth * _safe_growth_factor(
                    growth_factors,
                    region,
                    "2029 DC Factor",
                    1.0,
                )

            available_engineers = opening_engineers * (
                1 - attrition_pct / 100.0
            )

            forecast_bau_hours = base_bau_hours * (
                1 + bau_growth_pct / 100.0
            )

            forecast_dc_hours = base_dc_hours * (
                1 + dc_growth_pct / 100.0
            )

            forecast_total_hours = forecast_bau_hours + forecast_dc_hours

            bau_required_engineers = forecast_bau_hours / engineer_capacity
            dc_required_engineers = forecast_dc_hours / engineer_capacity

            required_engineers_before_buffer = (
                bau_required_engineers + dc_required_engineers
            )

            combined_required_engineers = required_engineers_before_buffer * (
                1 + _safe_number(planning_buffer_pct) / 100.0
            )

            combined_additional_required = max(
                math.ceil(combined_required_engineers - available_engineers),
                0,
            )

            ending_engineers_after_hiring = (
                available_engineers + combined_additional_required
            )

            shortage_surplus = available_engineers - combined_required_engineers

            results.append(
                {
                    "Region": region,
                    "Product": product,
                    "Year": year,

                    "Capacity Mode": capacity_mode,
                    "Capacity per Engineer": round(engineer_capacity, 2),
                    "Planning Buffer %": round(_safe_number(planning_buffer_pct), 2),

                    "Base BAU Hours": round(base_bau_hours, 2),
                    "Base DC Hours": round(base_dc_hours, 2),
                    "Base Total Hours": round(base_total_hours, 2),

                    "Forecast BAU Hours": round(forecast_bau_hours, 2),
                    "Forecast DC Hours": round(forecast_dc_hours, 2),
                    "Forecast Total Hours": round(forecast_total_hours, 2),

                    "BAU Growth %": round(bau_growth_pct, 2),
                    "DC Growth %": round(dc_growth_pct, 2),

                    "Opening Engineers": round(opening_engineers, 2),
                    "Attrition %": round(attrition_pct, 2),
                    "Available Engineers": round(available_engineers, 2),

                    "BAU Required Engineers": round(bau_required_engineers, 2),
                    "DC Incremental Engineers": round(dc_required_engineers, 2),
                    "Required Before Buffer": round(required_engineers_before_buffer, 2),
                    "Combined Required Engineers": round(combined_required_engineers, 2),

                    "Shortage / Surplus": round(shortage_surplus, 2),
                    "Capacity Status": _capacity_status(shortage_surplus),

                    "Combined Additional Required": int(combined_additional_required),

                    "Ending Engineers After Hiring": round(
                        ending_engineers_after_hiring,
                        2,
                    ),
                }
            )

            opening_engineers = ending_engineers_after_hiring
            previous_bau_growth = bau_growth_pct
            previous_dc_growth = dc_growth_pct

    return pd.DataFrame(results)
