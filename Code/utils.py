import pandas as pd


def load_data(file):
    """
    Load CSV file and preprocess basic columns.
    """
    df = pd.read_csv(file, parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    return df


def preprocess_data(df):
    """
    Preprocess manually entered DataFrame.
    """
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    return df


def compute_kpis(df):
    if df.empty:
        return 0, 0, 0, 0

    df["Month"] = df["Date"].dt.to_period("M")

    # Income is total salary
    months_count = df["Month"].nunique()
    total_income = df[df["Category"] == "Salary"]["Amount"].sum()

    # Expenses: sum of negative amounts only
    total_expense = (
        df[df["Amount"] < 0]["Amount"].abs().sum() / months_count
        if months_count > 0
        else 0
    )

    income = total_income / months_count if months_count > 0 else 0

    savings = income - total_expense
    savings_rate = (savings / income * 100) if total_income > 0 else 0

    return income, total_expense, savings, savings_rate


def months_sorted(series):
    """Sort months chronologically and return as comma-separated abbreviations."""
    return ", ".join(series.sort_values().dt.strftime("%b"))


def describe_cluster(avg, q1, q2):
    """Return cluster description based on average spending."""
    if avg < q1:
        return "Low spending month"
    elif avg < q2:
        return "Medium spending month"
    else:
        return "High spending month"


def color_dot(cluster, cluster_colors):
    """Return HTML for colored dot matching cluster color."""
    color = cluster_colors.get(cluster, "gray")
    return f"<span style='color:{color}; font-size:20px;'>&#9679;</span>"
