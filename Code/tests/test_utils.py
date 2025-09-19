import pytest
import pandas as pd
from io import StringIO
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


def test_load_data_basic():
    """Test that load_data reads CSV correctly and adds 'Month' column."""
    csv_content = """Date,Category,Amount
    2025-01-01,Salary,1000
    2025-01-15,Groceries,-200"""
    fake_file = StringIO(csv_content)
    df = load_data(fake_file)

    # Check columns
    assert "Date" in df.columns
    assert "Category" in df.columns
    assert "Amount" in df.columns
    assert "Month" in df.columns

    # Check types
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert pd.api.types.is_period_dtype(df["Month"])

    # Check data correctness
    assert df.shape[0] == 2
    assert df["Month"].iloc[0] == pd.Timestamp("2025-01-01").to_period("M")
    assert df["Month"].iloc[1] == pd.Timestamp("2025-01-15").to_period("M")


def test_load_data_columns():
    """Test that loading CSV data creates a DataFrame with 'Date' as datetime
    and adds a 'Month' column correctly."""
    csv_content = (
        "Date,Category,Amount\n2025-01-01,Salary,1000\n2025-01-15,Groceries,-200"
    )
    fake_file = StringIO(csv_content)
    df = pd.read_csv(fake_file, parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df.shape[0] == 2


@pytest.fixture
def sample_df():
    """Fixture with multiple rows for testing KPI computation and preprocessing."""
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                ["2025-01-01", "2025-01-15", "2025-02-01", "2025-02-15"]
            ),
            "Category": ["Salary", "Groceries", "Salary", "Entertainment"],
            "Amount": [1000, -200, 2000, -300],
        }
    )
    return df


@pytest.fixture
def empty_df():
    """Fixture representing an empty DataFrame for edge case testing."""
    return pd.DataFrame(columns=["Date", "Category", "Amount"])


def test_preprocess_data_adds_month_column():
    """Test that preprocess_data converts 'Date' to datetime and adds 'Month' column."""
    df = pd.DataFrame({"Date": ["2025-03-01"]})
    df = preprocess_data(df)
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["Month"].iloc[0].month == 3


def test_compute_kpis_multiple_months(sample_df):
    """Test KPI computation over multiple months with both income and expenses."""
    income, expense, savings, rate = compute_kpis(sample_df)
    assert income == pytest.approx(1500)  # 3000 total salary / 2 months
    assert expense == pytest.approx(250)  # 500 total expenses / 2 months
    assert savings == pytest.approx(1250)
    assert rate == pytest.approx(1250 / 1500 * 100)


def test_compute_kpis_no_salary():
    """Test KPI computation when there is no salary; income should be 0."""
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


def test_compute_kpis_empty(empty_df):
    """Test KPI computation on an empty DataFrame returns all zeros."""
    assert compute_kpis(empty_df) == (0, 0, 0, 0)


def test_months_sorted_duplicates():
    """Test that months_sorted correctly sorts months chronologically and formats as abbreviations."""
    s = pd.Series(pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01"]))
    result = months_sorted(s)
    assert result == "Jan, Jan, Feb"


def test_months_sorted_empty():
    """Test that months_sorted returns an empty string for empty input."""
    s = pd.Series(dtype="datetime64[ns]")
    assert months_sorted(s) == ""


def test_describe_cluster_boundaries():
    """Test describe_cluster returns correct descriptions based on average value boundaries."""
    assert describe_cluster(100, 100, 200) == "Medium spending month"
    assert describe_cluster(200, 100, 200) == "High spending month"


def test_color_dot_known_unknown():
    """Test color_dot returns the correct HTML dot color for known and unknown clusters."""
    colors = {"Low": "green", "High": "red"}
    assert "green" in color_dot("Low", colors)
    assert "gray" in color_dot("Medium", colors)
    html = color_dot("High", colors)
    assert html.startswith("<span") and "&#9679;" in html
