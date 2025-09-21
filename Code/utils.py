# -----------------------------------------------------------------------------
# Finance Intelligence Dashboard
# Copyright (c) 2025 Nandana Sreeraj
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
# -----------------------------------------------------------------------------


import pandas as pd
from pandas import DataFrame, Series
from typing import Tuple, Dict


def load_data(file: str) -> DataFrame:
    """
    Load a CSV file into a DataFrame and preprocess it.

    The "Date" column is parsed as datetime, and a "Month" column
    representing the monthly period of each transaction is added.

    Args:
        file: Path to the CSV file.

    Returns:
        DataFrame with parsed dates and a "Month" column.
    """
    df = pd.read_csv(file, parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    return df


def preprocess_data(df: DataFrame) -> DataFrame:
    """
    Preprocess a manually created DataFrame to ensure proper date handling.

    Converts the "Date" column to datetime and adds a "Month" column.

    Args:
        df: Input DataFrame with at least a "Date" column.

    Returns:
        DataFrame with "Date" parsed and a "Month" column added.
    """
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    return df


def compute_kpis(df: DataFrame) -> Tuple[float, float, float, float]:
    """
    Compute financial KPIs (income, expenses, savings, savings rate).

    KPIs are calculated on a monthly basis:
    - Income: Average monthly income (Category == "Salary").
    - Expenses: Average monthly expenses (absolute values of negatives).
    - Savings: Income - Expenses.
    - Savings Rate: (Savings / Income) * 100.

    Args:
        df: DataFrame with "Date", "Category", and "Amount" columns.

    Returns:
        A tuple of four floats:
            income: Average monthly income.
            total_expense: Average monthly expenses.
            savings: Average monthly savings.
            savings_rate: Savings as a percentage of income.
    """
    if df.empty:
        return 0, 0, 0, 0

    df["Month"] = df["Date"].dt.to_period("M")
    months_count = df["Month"].nunique()

    total_income = df[df["Category"] == "Salary"]["Amount"].sum()
    total_expense = (
        df[df["Amount"] < 0]["Amount"].abs().sum() / months_count
        if months_count > 0
        else 0
    )
    income = total_income / months_count if months_count > 0 else 0

    savings = income - total_expense
    savings_rate = (savings / income * 100) if total_income > 0 else 0

    return income, total_expense, savings, savings_rate


def months_sorted(series: Series) -> str:
    """
    Sort months chronologically and return them as a comma-separated string.

    Args:
        series: Series of datetime-like objects.

    Returns:
        Comma-separated string of month abbreviations.
    """
    return ", ".join(series.sort_values().dt.strftime("%b"))


def describe_cluster(avg: float, q1: float, q2: float) -> str:
    """
    Return a description of a spending cluster based on thresholds.

    Args:
        avg: Average monthly spending for the cluster.
        q1: First quartile threshold.
        q2: Second quartile threshold.

    Returns:
        A label describing the spending pattern ("Low", "Medium", or "High").
    """
    if avg < q1:
        return "Low spending month"
    elif avg < q2:
        return "Medium spending month"
    else:
        return "High spending month"


def color_dot(cluster: str, cluster_colors: Dict[str, str]) -> str:
    """
    Generate an HTML span element for a colored dot representing a cluster.

    Args:
        cluster: Cluster label.
        cluster_colors: Mapping of cluster names to color strings.

    Returns:
        HTML string for a colored dot.
    """
    color = cluster_colors.get(cluster, "gray")
    return f"<span style='color:{color}; font-size:20px;'>&#9679;</span>"
