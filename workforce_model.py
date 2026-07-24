import math
import pandas as pd


def calculate_workforce(
    df,
    growth_parameters,
    attrition_parameters,
    productive_hours,
    working_days,
    target_utilization,
    forecast_years=None,
    hiring_split_parameters=None,
):
    """
    Creates a rolling 3-year workforce forecast.

    Output is one row per Forecast Year + Region + Product.

    Logic:
    Opening SE
    - Attrition
    + H1 Hiring
    + H2 Hiring
    = Closing SE

    Closing SE becomes next year's Opening SE.
    """

    if forecast_years is None:
        forecast_years = [2027, 2028, 2029]

    if hiring_split_parameters is None:
        hiring_split_parameters = {
            int(year): {"H1": 50.0, "H2": 50.0}
            for year in forecast_years
        }

    annual_capacity = productive_hours * working_days * 12
    effective_capacity = annual_capacity * target_utilization / 100

    results = []

    for _, row in df.iterrows():
        region = row["Region"]
        product = row["Product"]

        opening_engineers = float(row["Current_SE"])

        current_hours = (
            row["Breakdown_WO"] * row["Breakdown_Hrs"]
            + row["PM_WO"] * row["PM_Hrs"]
            + row["Startup_WO"] * row["Startup_Hrs"]
        )

        growth = growth_parameters.get(region, {}).get(
            product,
            {"BAU": 0.0, "DC": 0.0},
        )

        bau_growth = float(growth.get("BAU", 0.0))
        dc_growth = float(growth.get("DC", 0.0))
        total_growth = bau_growth + dc_growth
        attrition = float(attrition_parameters.get(product, 8.0))

        for year_index, forecast_year in enumerate(forecast_years, start=1):
            split = hiring_split_parameters.get(
                int(forecast_year),
                {"H1": 50.0, "H2": 50.0},
            )

            h1_percent = float(split.get("H1", 50.0))
            h2_percent = float(split.get("H2", 50.0))

            available_engineers = opening_engineers * (1 - attrition / 100)

            bau_future_hours = current_hours * ((1 + bau_growth / 100) ** year_index)
            combined_future_hours = current_hours * ((1 + total_growth / 100) ** year_index)
            dc_incremental_hours = max(combined_future_hours - bau_future_hours, 0)

            current_required_engineers = current_hours / effective_capacity
            bau_required_engineers = bau_future_hours / effective_capacity
            dc_incremental_engineers = dc_incremental_hours / effective_capacity
            combined_required_engineers = combined_future_hours / effective_capacity

            gap = combined_required_engineers - available_engineers
            additional_required = max(math.ceil(gap), 0)

            h1_hiring = math.ceil(additional_required * h1_percent / 100)
            h2_hiring = max(additional_required - h1_hiring, 0)

            closing_engineers = available_engineers + h1_hiring + h2_hiring

            results.append(
                {
                    "Forecast Year": int(forecast_year),
                    "Region": region,
                    "Product": product,
                    "Opening SE": round(opening_engineers, 1),
                    "Attrition %": attrition,
                    "Available Engineers": round(available_engineers, 1),
                    "BAU Growth %": bau_growth,
                    "DC Growth %": dc_growth,
                    "Total Growth %": total_growth,
                    "Productive Hrs/Day": productive_hours,
                    "Working Days/Month": working_days,
                    "Utilization %": target_utilization,
                    "Annual Capacity": round(annual_capacity, 1),
                    "Effective Capacity": round(effective_capacity, 1),
                    "Current Hours": round(current_hours, 1),
                    "Current Required Engineers": round(current_required_engineers, 1),
                    "BAU Future Hours": round(bau_future_hours, 1),
                    "BAU Required Engineers": round(bau_required_engineers, 1),
                    "DC Incremental Hours": round(dc_incremental_hours, 1),
                    "DC Incremental Engineers": round(dc_incremental_engineers, 1),
                    "Combined Future Hours": round(combined_future_hours, 1),
                    "Combined Required Engineers": round(combined_required_engineers, 1),
                    "Combined Net Gap / Surplus": round(gap, 1),
                    "Combined Additional Required": int(additional_required),
                    "H1 Hiring %": h1_percent,
                    "H2 Hiring %": h2_percent,
                    "H1 Hiring": int(h1_hiring),
                    "H2 Hiring": int(h2_hiring),
                    "Closing SE": round(closing_engineers, 1),
                }
            )

            opening_engineers = closing_engineers

    return pd.DataFrame(results)
