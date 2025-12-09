#!/usr/bin/env python3
"""
event_day_additional_ridership.py

Estimate additional ridership per route on event days using Bus-Ridership.xlsx
and plot the top increases as a bar chart.
"""

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt  # <-- NEW

# --- Configuration -----------------------------------------------------------

DEFAULT_EXCEL_PATH = "Data/MARTA_Bus_Ridership_2023_20250912.xlsx"

EVENT_DATES_STR = [
    "June 29, 2025",
    "July 5, 2025",
    "December 30, 2023",
    "January 1, 2025",
    "December 2, 2023",
    "December 7, 2024",
    "August 31, 2024",
    "January 20, 2025",
    "July 26, 2023",
    "June 20, 2024",
    "May 27, 2023",
]

OUTPUT_CSV = "event_day_additional_ridership_by_route.csv"
OUTPUT_PNG = "event_day_top_route_increases.png"  # <-- NEW
TRIP_COLUMN = "Total trips"
DATE_COLUMN = "Date"
ROUTE_COLUMN = "Route"


# --- Core logic --------------------------------------------------------------

def load_data(excel_path: Path) -> pd.DataFrame:
    """Load the Bus-Ridership Excel file into a DataFrame."""
    if not excel_path.exists():
        raise FileNotFoundError(
            f"Could not find Excel file at {excel_path}. "
            f"Update DEFAULT_EXCEL_PATH or pass a path as an argument."
        )

    df = pd.read_excel(excel_path)

    expected_cols = {DATE_COLUMN, ROUTE_COLUMN, TRIP_COLUMN}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Excel file is missing expected columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])

    return df


def label_event_days(df: pd.DataFrame) -> pd.DataFrame:
    """Add a boolean 'is_event' column to df marking the event dates."""
    event_dates = pd.to_datetime(EVENT_DATES_STR)
    df = df.copy()
    df["is_event"] = df[DATE_COLUMN].isin(event_dates)
    return df


def compute_additional_ridership_by_route(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute baseline vs event-day averages per route and additional ridership.

    Returns a DataFrame indexed by Route with columns:
    - BaselineMeanTrips
    - EventMeanTrips
    - AdditionalTrips
    - PercentChange
    """
    if "is_event" not in df.columns:
        raise ValueError("DataFrame must have an 'is_event' column. Run label_event_days first.")

    baseline_df = df[~df["is_event"]]
    event_df = df[df["is_event"]]

    baseline_stats = (
        baseline_df
        .groupby(ROUTE_COLUMN)[TRIP_COLUMN]
        .mean()
        .rename("BaselineMeanTrips")
    )
    event_stats = (
        event_df
        .groupby(ROUTE_COLUMN)[TRIP_COLUMN]
        .mean()
        .rename("EventMeanTrips")
    )

    results = pd.concat([baseline_stats, event_stats], axis=1)

    results["AdditionalTrips"] = results["EventMeanTrips"] - results["BaselineMeanTrips"]
    results["PercentChange"] = (
        results["AdditionalTrips"] / results["BaselineMeanTrips"] * 100
    )

    return results


def print_summary(df: pd.DataFrame, results: pd.DataFrame, top_n: int = 10) -> None:
    """Print a short summary to the terminal, including top increases."""
    num_event_dates = df[df["is_event"]][DATE_COLUMN].nunique()
    num_event_rows = df["is_event"].sum()
    num_routes = results.shape[0]

    print("=== Event-Day Additional Ridership per Route ===")
    print(f"Number of event dates:       {num_event_dates}")
    print(f"Number of event-day records: {num_event_rows}")
    print(f"Number of routes analyzed:   {num_routes}\n")

    baseline_overall = (
        df[~df["is_event"]]
        .groupby(DATE_COLUMN)[TRIP_COLUMN]
        .sum()
        .mean()
    )
    event_overall = (
        df[df["is_event"]]
        .groupby(DATE_COLUMN)[TRIP_COLUMN]
        .sum()
        .mean()
    )
    delta_overall = event_overall - baseline_overall
    pct_overall = delta_overall / baseline_overall * 100

    print("=== Systemwide impact of event days ===")
    print(f"Average baseline (non-event days): {baseline_overall:10.1f} trips/day")
    print(f"Average on event days:             {event_overall:10.1f} trips/day")
    print(f"Average increase (absolute):       {delta_overall:10.1f} trips/day")
    print(f"Average increase (percent):        {pct_overall:10.2f}%\n")

    # Top routes by additional trips
    print(f"Top {top_n} routes by additional trips on event days:")
    top_increase = (
        results
        .dropna(subset=["AdditionalTrips"])
        .sort_values("AdditionalTrips", ascending=False)
        .head(top_n)
    )
    for route, row in top_increase.iterrows():
        print(
            f"  Route {route}: "
            f"+{row['AdditionalTrips']:.1f} trips/day "
            f"({row['PercentChange']:.1f}% vs baseline)"
        )


# --- NEW: plotting -----------------------------------------------------------

def plot_top_increases(
    results: pd.DataFrame,
    top_n: int = 20,
    output_path: Path | None = None,
) -> None:
    """
    Plot a bar chart of the top `top_n` routes by AdditionalTrips.

    Saves to `output_path` if provided, otherwise just shows the plot.
    """
    top = (
        results
        .dropna(subset=["AdditionalTrips"])
        .sort_values("AdditionalTrips", ascending=False)
        .head(top_n)
    )

    if top.empty:
        print("No data available to plot (top increases DataFrame is empty).")
        return

    plt.figure(figsize=(10, 6))
    plt.bar(top.index.astype(str), top["AdditionalTrips"])
    plt.xlabel("Route")
    plt.ylabel("Additional trips per day (event - baseline)")
    plt.title(f"Top {top_n} Routes by Additional Ridership on Event Days")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if output_path is not None:
        plt.savefig(output_path, dpi=300)
        print(f"Saved bar chart to: {output_path}")
        plt.close()
    else:
        plt.show()


# --- Main --------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        excel_path = Path(sys.argv[1])
    else:
        excel_path = Path(DEFAULT_EXCEL_PATH)

    print(f"Loading ridership data from: {excel_path}")
    df = load_data(excel_path)
    df = label_event_days(df)

    results = compute_additional_ridership_by_route(df)

    # Save per-route stats
    output_csv_path = excel_path.parent / OUTPUT_CSV
    results.to_csv(output_csv_path, index=True)
    print(f"\nPer-route results saved to: {output_csv_path}\n")

    # Print textual summary (including top increases)
    print_summary(df, results, top_n=10)

    # Plot top increases
    output_png_path = excel_path.parent / OUTPUT_PNG
    plot_top_increases(results, top_n=20, output_path=output_png_path)


if __name__ == "__main__":
    main()
