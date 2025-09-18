import pytest
import pandas as pd
import sys
import os
import warnings

warnings.filterwarnings("ignore")  
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visualize import show_anomalies, forecast_expenses, spending_clusters

# Fixtures
@pytest.fixture
def expense_df():
    """3 months of expense data for anomalies and clustering tests."""
    df = pd.DataFrame({
        "Date": pd.to_datetime([
            "2025-01-01", "2025-01-15", "2025-02-01", "2025-02-15",
            "2025-03-01", "2025-03-15"
        ]),
        "Category": ["Salary", "Groceries", "Salary", "Entertainment", "Groceries", "Entertainment"],
        "Amount": [1000, -200, 2000, -300, -150, -250]
    })
    df["Month"] = df["Date"].dt.to_period("M")
    return df

@pytest.fixture
def expense_df_forecast():
    """6 months of expense data required for SARIMAX forecasting tests."""
    df = pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=6, freq="MS").tolist() +
                pd.date_range(start="2025-01-15", periods=6, freq="MS").tolist(),
        "Category": ["Groceries", "Entertainment"] * 6,
        "Amount": [-200, -150] * 6
    })
    df["Month"] = df["Date"].dt.to_period("M")
    return df

@pytest.fixture
def small_expense_df():
    """Only 2 months of expense data, used for testing forecast edge case (insufficient data)."""
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01"]),
        "Category": ["Groceries", "Entertainment", "Groceries"],
        "Amount": [-100, -200, -50]
    })
    df["Month"] = df["Date"].dt.to_period("M")
    return df

@pytest.fixture
def empty_df():
    """Empty DataFrame fixture for testing empty input handling."""
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Month"])

# Test functions
def test_show_anomalies_returns_dataframe(expense_df, empty_df):
    """Test that show_anomalies returns a DataFrame with an 'Anomaly' column for normal data,
    and returns an empty DataFrame for empty input."""
    anomalies = show_anomalies(expense_df)
    assert not anomalies.empty
    assert "Anomaly" in anomalies.columns

    anomalies_empty = show_anomalies(empty_df)
    assert anomalies_empty.empty

def test_forecast_expenses_returns_dataframe(expense_df_forecast):
    """Test that forecast_expenses returns a DataFrame with predicted expenses
    when enough monthly data is provided."""
    forecast_df = forecast_expenses(expense_df_forecast, forecast_months=2)
    assert not forecast_df.empty
    assert "Predicted_Expense" in forecast_df.columns
    assert len(forecast_df) == 2

def test_forecast_expenses_not_enough_data(small_expense_df):
    """Test that forecast_expenses returns an empty DataFrame when there are
    fewer than 6 months of data (insufficient for SARIMAX)."""
    forecast_df = forecast_expenses(small_expense_df, forecast_months=2)
    assert forecast_df.empty

def test_forecast_expenses_empty(empty_df):
    """Test that forecast_expenses returns an empty DataFrame when input is empty."""
    forecast_df = forecast_expenses(empty_df)
    assert forecast_df.empty

def test_spending_clusters_returns_dataframe(expense_df):
    """Test that spending_clusters returns a DataFrame with 'Amount' and 'Cluster' columns
    when valid expense data is provided."""
    monthly = spending_clusters(expense_df)
    assert not monthly.empty
    assert "Amount" in monthly.columns
    assert "Cluster" in monthly.columns

def test_spending_clusters_empty(empty_df):
    """Test that spending_clusters returns an empty or minimal DataFrame when input is empty."""
    monthly = spending_clusters(empty_df)
    assert monthly.empty or "Amount" in monthly.columns
