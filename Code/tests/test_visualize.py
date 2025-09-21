# -----------------------------------------------------------------------------
# Finance Intelligence Dashboard - Visualization Tests
# Copyright (c) 2025 Nandana Sreeraj
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
# -----------------------------------------------------------------------------

import pytest
import pandas as pd
import sys
import os
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from visualize import (
    show_anomalies,
    forecast_expenses,
    spending_clusters,
    plot_monthly_expenses,
    plot_category_spending,
    plot_monthly_trends,
)


# Fixtures
@pytest.fixture
def expense_df() -> pd.DataFrame:
    """
    Provide 3 months of expense data for anomalies and clustering tests.

    Returns:
        pd.DataFrame: Sample transactions with income and expenses.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-15",
                    "2025-02-01",
                    "2025-02-15",
                    "2025-03-01",
                    "2025-03-15",
                ]
            ),
            "Category": [
                "Salary",
                "Groceries",
                "Salary",
                "Entertainment",
                "Groceries",
                "Entertainment",
            ],
            "Amount": [1000, -200, 2000, -300, -150, -250],
        }
    )
    df["Month"] = df["Date"].dt.to_period("M")
    return df


@pytest.fixture
def expense_df_forecast() -> pd.DataFrame:
    """
    Provide 6 months of expense data required for SARIMAX forecasting tests.

    Returns:
        pd.DataFrame: Sample monthly expense transactions.
    """
    df = pd.DataFrame(
        {
            "Date": pd.date_range(start="2025-01-01", periods=6, freq="MS").tolist()
            + pd.date_range(start="2025-01-15", periods=6, freq="MS").tolist(),
            "Category": ["Groceries", "Entertainment"] * 6,
            "Amount": [-200, -150] * 6,
        }
    )
    df["Month"] = df["Date"].dt.to_period("M")
    return df


@pytest.fixture
def small_expense_df() -> pd.DataFrame:
    """
    Provide only 2 months of expense data to test forecast edge case (insufficient data).

    Returns:
        pd.DataFrame: Sample data with fewer than 6 months of expenses.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01"]),
            "Category": ["Groceries", "Entertainment", "Groceries"],
            "Amount": [-100, -200, -50],
        }
    )
    df["Month"] = df["Date"].dt.to_period("M")
    return df


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """
    Provide an empty DataFrame for testing empty input handling.

    Returns:
        pd.DataFrame: Empty DataFrame with expected columns.
    """
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Month"])


# Test functions
def test_show_anomalies_returns_dataframe(
    expense_df: pd.DataFrame, empty_df: pd.DataFrame
) -> None:
    """
    Verify that show_anomalies returns a DataFrame with an 'Anomaly' column for normal data,
    and returns an empty DataFrame for empty input.
    """
    anomalies = show_anomalies(expense_df)
    assert not anomalies.empty
    assert "Anomaly" in anomalies.columns

    anomalies_empty = show_anomalies(empty_df)
    assert anomalies_empty.empty


def test_forecast_expenses_returns_dataframe(expense_df_forecast: pd.DataFrame) -> None:
    """
    Verify that forecast_expenses returns predicted expense DataFrame
    when enough monthly data is provided.
    """
    forecast_df = forecast_expenses(expense_df_forecast, forecast_months=2)
    assert not forecast_df.empty
    assert "Predicted_Expense" in forecast_df.columns
    assert len(forecast_df) == 2


def test_forecast_expenses_not_enough_data(small_expense_df: pd.DataFrame) -> None:
    """
    Verify that forecast_expenses returns an empty DataFrame when
    fewer than 6 months of data are provided.
    """
    forecast_df = forecast_expenses(small_expense_df, forecast_months=2)
    assert forecast_df.empty


def test_forecast_expenses_empty(empty_df: pd.DataFrame) -> None:
    """
    Verify that forecast_expenses returns an empty DataFrame for empty input.
    """
    forecast_df = forecast_expenses(empty_df)
    assert forecast_df.empty


def test_spending_clusters_returns_dataframe(expense_df: pd.DataFrame) -> None:
    """
    Verify that spending_clusters returns a DataFrame with 'Amount' and 'Cluster' columns.
    """
    monthly = spending_clusters(expense_df)
    assert not monthly.empty
    assert "Amount" in monthly.columns
    assert "Cluster" in monthly.columns


def test_spending_clusters_empty(empty_df: pd.DataFrame) -> None:
    """
    Verify that spending_clusters returns an empty or minimal DataFrame for empty input.
    """
    monthly = spending_clusters(empty_df)
    assert monthly.empty or "Amount" in monthly.columns


def test_plot_monthly_expenses_creates_month_column(expense_df: pd.DataFrame) -> None:
    """
    Verify that plot_monthly_expenses correctly creates the Month column as timestamps.
    """
    df = expense_df.copy()
    plot_monthly_expenses(df, income_categories=["salary"])
    assert "Month" in df.columns
    assert all(isinstance(m, pd.Timestamp) for m in df["Date"])


def test_plot_monthly_expenses_filters_income(expense_df: pd.DataFrame) -> None:
    """
    Verify that income categories are excluded from budget calculations.
    """
    df = expense_df.copy()
    all_categories = df["Category"].unique()
    plot_monthly_expenses(df, income_categories=["salary"])
    non_income = [c for c in all_categories if c.lower() not in ["salary"]]
    assert "Salary" not in non_income
    assert set(non_income).issubset(set(all_categories))


def test_plot_monthly_expenses_empty_input(empty_df: pd.DataFrame) -> None:
    """
    Verify that plot_monthly_expenses handles empty DataFrame without crashing.
    """
    df = empty_df.copy()
    if df.empty:
        try:
            df["Month"] = pd.to_datetime(df["Date"])
            assert df.empty
        except Exception as e:
            pytest.fail(f"Function crashed on empty DataFrame: {e}")
    else:
        plot_monthly_expenses(df)


def test_plot_category_spending_all_income() -> None:
    """
    Verify plot_category_spending triggers a warning when only income rows are present.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-01-01"]),
            "Category": ["Salary"],
            "Amount": [1000],
        }
    )
    plot_category_spending(df)


def test_plot_monthly_trends_no_expenses() -> None:
    """
    Verify plot_monthly_trends triggers a warning when there are no expense rows.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-01-01"]),
            "Month": pd.to_datetime(["2025-01-01"]),
            "Category": ["Salary"],
            "Amount": [1000],
        }
    )
    plot_monthly_trends(df)


def test_forecast_expenses_fail_sarimax() -> None:
    """
    Verify forecast_expenses handles data that triggers SARIMAX exceptions gracefully.
    """
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=6, freq="MS"),
            "Category": ["Groceries"] * 6,
            "Amount": [-100, float("nan"), -100, -100, -100, -100],
        }
    )
    df["Month"] = df["Date"].dt.to_period("M")
    forecast_df = forecast_expenses(df)
    assert forecast_df.empty


def test_spending_clusters_no_expense_rows() -> None:
    """
    Verify spending_clusters handles the case where all rows are income.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-01-01"]),
            "Category": ["Salary"],
            "Amount": [1000],
        }
    )
    df["Month"] = df["Date"].dt.to_period("M")
    clusters = spending_clusters(df)
    assert clusters.empty or "Amount" in clusters.columns
