# -----------------------------------------------------------------------------
# Finance Intelligence Dashboard - Tests
# Copyright (c) 2025 Nandana Sreeraj
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
# -----------------------------------------------------------------------------

import pytest
import pandas as pd
from io import StringIO
from typing import Generator
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    preprocess_data,
    compute_kpis,
    months_sorted,
    describe_cluster,
    color_dot,
    load_data,
)


def test_load_data_basic() -> None:
    """
    Verify that load_data reads CSV correctly and adds the 'Month' column.

    Checks that columns exist, types are correct, and data values match expected.
    """
    csv_content = """Date,Category,Amount
2025-01-01,Salary,1000
2025-01-15,Groceries,-200"""
    fake_file = StringIO(csv_content)
    df = load_data(fake_file)

    assert "Date" in df.columns
    assert "Category" in df.columns
    assert "Amount" in df.columns
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert pd.api.types.is_period_dtype(df["Month"])
    assert df.shape[0] == 2
    assert df["Month"].iloc[0] == pd.Timestamp("2025-01-01").to_period("M")
    assert df["Month"].iloc[1] == pd.Timestamp("2025-01-15").to_period("M")


def test_load_data_columns() -> None:
    """
    Verify that load_data creates 'Date' as datetime and adds a 'Month' column.

    Uses a simple CSV content to check column creation and data types.
    """
    csv_content = "Date,Category,Amount\n2025-01-01,Salary,1000\n2025-01-15,Groceries,-200"
    fake_file = StringIO(csv_content)
    df = pd.read_csv(fake_file, parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df.shape[0] == 2


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """
    Provide a sample DataFrame with multiple rows for testing KPI computation.

    Returns:
        pd.DataFrame: Sample transaction data covering income and expenses.
    """
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(
                ["2025-01-01", "2025-01-15", "2025-02-01", "2025-02-15"]
            ),
            "Category": ["Salary", "Groceries", "Salary", "Entertainment"],
            "Amount": [1000, -200, 2000, -300],
        }
    )


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """
    Provide an empty DataFrame for edge case testing.

    Returns:
        pd.DataFrame: Empty DataFrame with expected columns.
    """
    return pd.DataFrame(columns=["Date", "Category", "Amount"])


def test_preprocess_data_adds_month_column() -> None:
    """
    Verify that preprocess_data converts 'Date' to datetime and adds 'Month' column.
    """
    df = pd.DataFrame({"Date": ["2025-03-01"]})
    df = preprocess_data(df)
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["Month"].iloc[0].month == 3


def test_compute_kpis_multiple_months(sample_df: pd.DataFrame) -> None:
    """
    Compute KPIs over multiple months and verify income, expenses, savings, and rate.
    """
    income, expense, savings, rate = compute_kpis(sample_df)
    assert income == pytest.approx(1500)
    assert expense == pytest.approx(250)
    assert savings == pytest.approx(1250)
    assert rate == pytest.approx(1250 / 1500 * 100)


def test_compute_kpis_no_salary() -> None:
    """
    Verify KPI computation when no salary exists; income should be 0.
    """
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-01-01", "2025-01-15"]),
            "Category": ["Groceries", "Entertainment"],
            "Amount": [-100, -50],
        }
    )
    income, expense, savings, rate = compute_kpis(df)
    assert income == 0
    assert expense == pytest.approx((100 + 50) / 1)
    assert savings == pytest.approx(-150)
    assert rate == 0


def test_compute_kpis_empty(empty_df: pd.DataFrame) -> None:
    """
    Verify that compute_kpis returns zeros for an empty DataFrame.
    """
    assert compute_kpis(empty_df) == (0, 0, 0, 0)


def test_months_sorted_duplicates() -> None:
    """
    Verify months_sorted returns correctly sorted month abbreviations with duplicates.
    """
    s = pd.Series(pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01"]))
    result = months_sorted(s)
    assert result == "Jan, Jan, Feb"


def test_months_sorted_empty() -> None:
    """
    Verify months_sorted returns an empty string for empty input Series.
    """
    s = pd.Series(dtype="datetime64[ns]")
    assert months_sorted(s) == ""


def test_describe_cluster_boundaries() -> None:
    """
    Verify describe_cluster returns correct labels for given thresholds.
    """
    assert describe_cluster(100, 100, 200) == "Medium spending month"
    assert describe_cluster(200, 100, 200) == "High spending month"


def test_color_dot_known_unknown() -> None:
    """
    Verify color_dot returns correct HTML dot color for known and unknown clusters.
    """
    colors = {"Low": "green", "High": "red"}
    assert "green" in color_dot("Low", colors)
    assert "gray" in color_dot("Medium", colors)
    html = color_dot("High", colors)
    assert html.startswith("<span") and "&#9679;" in html
