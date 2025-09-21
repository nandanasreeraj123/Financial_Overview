# -----------------------------------------------------------------------------
# Finance Intelligence Dashboard
# Copyright (c) 2025 Nandana Sreeraj
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
# -----------------------------------------------------------------------------


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from statsmodels.tsa.statespace.sarimax import SARIMAX
from utils import months_sorted, color_dot, describe_cluster
import altair as alt
from pandas import DataFrame
from typing import Dict, List, Union


def plot_category_spending(df: DataFrame) -> None:
    """
    Display a pie chart of expenses by category (excluding Salary).

    Negative amounts are treated as expenses and converted to positive values.
    If the dataset is empty or contains no expenses, warnings are displayed.

    Args:
        df: DataFrame with at least "Category" and "Amount" columns.

    Returns:
        None. Displays a Plotly pie chart in Streamlit.
    """
    if df.empty:
        st.warning("No data to plot category spending.")
        return

    expenses = df[(df["Category"] != "Salary") & (df["Amount"] < 0)].copy()
    expenses["Amount"] = expenses["Amount"].abs()

    if expenses.empty:
        st.warning("No expense data to plot.")
        return

    cat_sum = expenses.groupby("Category")["Amount"].sum().reset_index()

    fig = px.pie(
        cat_sum,
        values="Amount",
        names="Category",
        hole=0.45,
        title="Spending by Category (Expenses Only)",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_monthly_trends(df: DataFrame) -> None:
    """
    Display a line chart showing monthly expense trends.

    Args:
        df: DataFrame with at least "Date" and "Amount" columns.

    Returns:
        None. Displays a Plotly line chart in Streamlit.
    """
    if df.empty:
        st.warning("No data to plot monthly trends.")
        return

    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()

    monthly = expenses.groupby(expenses["Month"])["Amount"].sum().reset_index()
    monthly["Month"] = monthly["Month"].astype(str)

    if monthly.empty:
        st.warning("No expense data to plot monthly trends.")
        return

    fig = px.line(
        monthly,
        x="Month",
        y="Amount",
        markers=True,
        title="Monthly Spending Trend (Expenses Only)",
        line_shape="spline",
        color_discrete_sequence=["#FF5733"],
    )
    st.plotly_chart(fig, use_container_width=True)


def show_anomalies(df: DataFrame) -> DataFrame:
    """
    Detect anomalies in transaction data using Isolation Forest.

    Args:
        df: DataFrame with "Date" and "Amount" columns.

    Returns:
        DataFrame containing transactions flagged as anomalies.
    """
    if df.empty:
        st.warning("No data to detect anomalies.")
        return pd.DataFrame()

    iso = IsolationForest(contamination=0.05, random_state=42)
    df["Anomaly"] = iso.fit_predict(df[["Amount"]])
    anomalies = df[df["Anomaly"] == -1]

    fig = px.scatter(
        df,
        x="Date",
        y="Amount",
        color=df["Anomaly"].map({1: "Normal", -1: "Anomaly"}),
        title="Expense Anomalies",
        color_discrete_map={"Normal": "blue", "Anomaly": "red"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("🚨 Anomalous Transactions:")
    st.dataframe(anomalies)
    return anomalies


def forecast_expenses(df: DataFrame, forecast_months: int = 6) -> DataFrame:
    """
    Forecast future monthly expenses using SARIMAX.

    Args:
        df: DataFrame with "Date" and "Amount" columns.
        forecast_months: Number of months to forecast (default = 6).

    Returns:
        DataFrame with forecasted values and confidence intervals.
    """
    if df.empty:
        st.warning("No data to forecast expenses.")
        return pd.DataFrame()

    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    monthly = expenses.groupby(expenses["Date"].dt.to_period("M"))["Amount"].sum()
    monthly.index = monthly.index.to_timestamp()

    if len(monthly) < 6:
        st.warning("Not enough monthly data for ARIMA forecasting.")
        return pd.DataFrame()

    try:
        model = SARIMAX(monthly, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        results = model.fit(disp=False)
    except Exception as e:
        st.error(f"Forecasting error: {e}")
        return pd.DataFrame()

    forecast = results.get_forecast(steps=forecast_months)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()

    forecast_df = pd.DataFrame(
        {
            "Month": forecast_mean.index.strftime("%Y-%m"),
            "Predicted_Expense": forecast_mean.values,
            "Lower_CI": forecast_ci.iloc[:, 0].values,
            "Upper_CI": forecast_ci.iloc[:, 1].values,
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=monthly.index.strftime("%Y-%m"), y=monthly.values, name="Actual")
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["Month"],
            y=forecast_df["Predicted_Expense"],
            mode="lines+markers",
            name="Forecast",
            line=dict(dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["Month"],
            y=forecast_df["Upper_CI"],
            mode="lines",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["Month"],
            y=forecast_df["Lower_CI"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(0,100,80,0.2)",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=f"📈 {forecast_months}-Month Expense Forecast",
        xaxis_title="Month",
        yaxis_title="Expense (€)",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    return forecast_df


def spending_clusters(df: DataFrame) -> DataFrame:
    """
    Cluster monthly expenses using KMeans and explain results.

    Args:
        df: DataFrame with "Date", "Amount", and "Month" columns.

    Returns:
        DataFrame containing monthly expenses with cluster assignments.
    """
    if df.empty:
        st.warning("No data to perform clustering.")
        return pd.DataFrame()

    monthly_expenses = df[df["Amount"] < 0].copy()
    monthly_expenses["Amount"] = monthly_expenses["Amount"].abs()

    monthly = (
        monthly_expenses.groupby(monthly_expenses["Month"])["Amount"]
        .sum()
        .reset_index()
    )
    monthly["Month"] = monthly["Month"].astype(str)
    monthly["Month_dt"] = pd.to_datetime(monthly["Month"].astype(str) + "-01")

    n_samples = len(monthly)
    n_clusters = min(3, n_samples)
    if n_clusters < 1:
        st.warning("Not enough data to perform clustering.")
        return monthly

    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(monthly[["Amount"]])
    monthly["Cluster"] = kmeans.labels_.astype(str)

    cluster_colors = {
        "0": "rgb(220, 20, 60)",
        "1": "rgb(34, 139, 34)",
        "2": "rgb(30, 144, 255)",
    }

    fig = px.scatter(
        monthly,
        x="Month",
        y="Amount",
        color="Cluster",
        title="Spending Clusters",
        color_discrete_map=cluster_colors,
    )
    st.plotly_chart(fig, use_container_width=True)

    cluster_summary = (
        monthly.groupby("Cluster")
        .agg({"Amount": "mean", "Month_dt": months_sorted})
        .reset_index()
    )

    q1 = cluster_summary["Amount"].quantile(0.33)
    q2 = cluster_summary["Amount"].quantile(0.66)

    cluster_summary["Description"] = cluster_summary["Amount"].apply(
        lambda x: describe_cluster(x, q1, q2)
    )
    cluster_summary["Color"] = cluster_summary["Cluster"].apply(
        lambda x: color_dot(x, cluster_colors)
    )

    cluster_summary = cluster_summary[
        ["Cluster", "Description", "Amount", "Month_dt", "Color"]
    ].rename(columns={"Month_dt": "Months"})

    st.subheader("Cluster Explanations (Jan → Dec)")
    st.write("Color column shows the cluster dot color in the scatter plot:")
    st.markdown(
        cluster_summary.to_html(escape=False, index=False), unsafe_allow_html=True
    )

    return monthly


def plot_monthly_expenses(
    df: DataFrame, income_categories: List[str] = ["salary"]
) -> None:
    """
    Compare monthly expenses against expected budgets interactively.

    Args:
        df: DataFrame with "Date", "Category", and "Amount" columns.
        income_categories: Categories considered income (default = ["salary"]).

    Returns:
        None. Displays interactive sliders, charts, and insights in Streamlit.
    """
    st.markdown(
        "<h3><i class='fa-solid fa-calendar'></i> Monthly Expenses vs Expected</h3>",
        unsafe_allow_html=True,
    )

    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()

    month_map = {d.strftime("%b %Y"): d for d in df["Month"].unique()}
    selected_label = st.selectbox("Select Month", list(month_map.keys()))
    selected_month = month_map[selected_label]

    month_df = df[df["Month"] == selected_month]
    month_df = month_df[
        ~month_df["Category"].str.lower().isin(income_categories)
    ].copy()
    month_df["Amount"] = month_df["Amount"].abs()

    st.markdown("### Set Expected Budget per Category")

    cols = st.columns(4)
    expected_dict: Dict[str, Union[int, float]] = {}
    categories = month_df["Category"].unique()

    for i, cat in enumerate(categories):
        col = cols[i % 4]
        expected_dict[cat] = col.slider(
            label=f"{cat} Expected (€)", min_value=0, max_value=5000, value=500, step=50
        )

    total_expected = sum(expected_dict.values())
    st.markdown(f"**Total Expected:** €{total_expected:,.2f}")

    chart_df = pd.DataFrame(
        {
            "Category": categories,
            "Expected": [expected_dict[c] for c in categories],
            "Actual": [
                month_df[month_df["Category"] == c]["Amount"].sum() for c in categories
            ],
        }
    )

    base = alt.Chart(chart_df).encode(y=alt.Y("Category:N", sort="-x"))
    expected_bar = base.mark_bar(color="lightgray").encode(x="Expected:Q")
    actual_bar = base.mark_bar(color="steelblue").encode(x="Actual:Q")
    st.altair_chart(expected_bar + actual_bar, use_container_width=True)

    category_spending = (
        month_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    )
    top3 = category_spending.head(3)

    st.markdown("### Top 3 Insights")
    for i, (cat, amt) in enumerate(top3.items(), start=1):
        st.markdown(f"**{i}. {cat}: €{amt:,.2f} spent**")
