import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import numpy as np

# =============================
# Utility Functions
# =============================

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
    total_expense = df[df["Amount"] < 0]["Amount"].abs().sum() / months_count if months_count > 0 else 0

    
    income = total_income / months_count if months_count > 0 else 0

    savings = income - total_expense
    savings_rate = (savings / income * 100) if total_income > 0 else 0

    return income, total_expense, savings, savings_rate

# =============================
# Visualization Functions
# =============================

def plot_category_spending(df):
    """
    Plot a pie chart of expenses by category (exclude Salary, show positive values).
    """
    if df.empty:
        st.warning("No data to plot category spending.")
        return

    # Keep only expense rows (exclude Salary & convert to positive values)
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
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_monthly_trends(df):
    """
    Plot line chart of monthly spending trends.
    """
    if df.empty:
        st.warning("No data to plot monthly trends.")
        return
    monthly = df.groupby(df["Month"])["Amount"].sum().reset_index()
    monthly["Month"] = monthly["Month"].astype(str)
    fig = px.line(monthly, x="Month", y="Amount", markers=True,
                  title="Monthly Spending Trend")
    st.plotly_chart(fig, use_container_width=True)

def show_anomalies(df):
    """
    Detect and visualize anomalies using Isolation Forest.
    """
    if df.empty:
        st.warning("No data to detect anomalies.")
        return pd.DataFrame()
    iso = IsolationForest(contamination=0.05, random_state=42)
    df["Anomaly"] = iso.fit_predict(df[["Amount"]])
    anomalies = df[df["Anomaly"] == -1]

    fig = px.scatter(df, x="Date", y="Amount", color=df["Anomaly"].map({1: "Normal", -1: "Anomaly"}),
                     title="Expense Anomalies", color_discrete_map={"Normal": "blue", "Anomaly": "red"})
    st.plotly_chart(fig, use_container_width=True)

    st.write("🚨 Anomalous Transactions:")
    st.dataframe(anomalies)
    return anomalies

from statsmodels.tsa.statespace.sarimax import SARIMAX

def forecast_expenses(df, forecast_months=6):
    """
    Forecast future monthly expenses using ARIMA/SARIMA.
    """
    if df.empty:
        st.warning("No data to forecast expenses.")
        return pd.DataFrame()

    # Keep only expenses
    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()

    # Aggregate to monthly totals
    monthly = expenses.groupby(expenses["Date"].dt.to_period("M"))["Amount"].sum()
    monthly.index = monthly.index.to_timestamp()  # convert PeriodIndex to Timestamp

    if len(monthly) < 6:
        st.warning("Not enough monthly data for ARIMA forecasting.")
        return pd.DataFrame()

    # Fit ARIMA (SARIMA for monthly seasonality)
    try:
        model = SARIMAX(monthly, order=(1,1,1), seasonal_order=(1,1,1,12))
        results = model.fit(disp=False)
    except Exception as e:
        st.error(f"Forecasting error: {e}")
        return pd.DataFrame()

    # Forecast future months
    forecast = results.get_forecast(steps=forecast_months)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()

    forecast_df = pd.DataFrame({
        "Month": forecast_mean.index.strftime("%Y-%m"),
        "Predicted_Expense": forecast_mean.values,
        "Lower_CI": forecast_ci.iloc[:, 0].values,
        "Upper_CI": forecast_ci.iloc[:, 1].values
    })

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly.index.strftime("%Y-%m"), y=monthly.values, name="Actual"))
    fig.add_trace(go.Scatter(x=forecast_df["Month"], y=forecast_df["Predicted_Expense"],
                             mode="lines+markers", name="Forecast", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=forecast_df["Month"], y=forecast_df["Upper_CI"],
                             mode="lines", name="Upper CI", line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=forecast_df["Month"], y=forecast_df["Lower_CI"],
                             mode="lines", name="Lower CI", line=dict(width=0), fill="tonexty", fillcolor="rgba(0,100,80,0.2)", showlegend=False))

    fig.update_layout(
        title=f"📈 {forecast_months}-Month Expense Forecast",
        xaxis_title="Month",
        yaxis_title="Expense (€)",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    return forecast_df


def spending_clusters(df):
    """
    Cluster monthly spending using KMeans and visualize clusters with custom RGB colors.
    """
    if df.empty:
        st.warning("No data to perform clustering.")
        return pd.DataFrame()
    
    monthly = df.groupby(df["Month"])["Amount"].sum().reset_index()
    monthly["Month"] = monthly["Month"].astype(str)

    n_samples = len(monthly)
    n_clusters = min(3, n_samples)  # max 3 clusters
    if n_clusters < 1:
        st.warning("Not enough data to perform clustering.")
        return monthly

    # Run KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(monthly[["Amount"]])
    monthly["Cluster"] = kmeans.labels_.astype(str)   # convert to string!

    # Assign custom RGB colors (string keys)
    cluster_colors = {
        "0": "rgb(220, 20, 60)",   # crimson red
        "1": "rgb(34, 139, 34)",   # forest green
        "2": "rgb(30, 144, 255)"   # dodger blue
    }

    fig = px.scatter(
        monthly,
        x="Month",
        y="Amount",
        color="Cluster",
        title="Spending Clusters",
        color_discrete_map=cluster_colors
    )
    st.plotly_chart(fig, use_container_width=True)
    return monthly



# =============================
# Streamlit App
# =============================

def main():
    st.set_page_config(page_title="💰 Finance Intelligence Dashboard", layout="wide")

    # Custom CSS
    st.markdown("""
        <style>
        .main { background-color: #f4f6f9; }
        .metric-card {
            padding: 15px; border-radius: 15px; background: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center;
        }
        .metric-value { font-size: 26px; font-weight: bold; color: #1E88E5; }
        .metric-label { font-size: 14px; color: gray; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("⚙️ Filters")
    st.sidebar.info("Use filters to customize your analysis")

    # Input Selection
    input_method = st.sidebar.radio("Data Source:", ["📂 Upload CSV", "✍️ Enter Manually"])

    df = None
    if input_method == "📂 Upload CSV":
        file = st.sidebar.file_uploader("Upload transactions CSV", type=["csv"])
        if file:
            df = load_data(file)
    else:
        st.sidebar.write("Manual entry mode")
        # Empty editor
        df = st.data_editor(pd.DataFrame(columns=["Date","Description","Category","Amount"]), num_rows="dynamic")
        if not df.empty:
            df = preprocess_data(df)

    if df is not None and not df.empty:
        # Sidebar Filters
        categories = st.sidebar.multiselect("Filter by Category", df["Category"].unique(), default=df["Category"].unique())
        df = df[df["Category"].isin(categories)]
        date_range = st.sidebar.date_input("Date Range", [df["Date"].min(), df["Date"].max()])
        df = df[(df["Date"] >= pd.to_datetime(date_range[0])) & (df["Date"] <= pd.to_datetime(date_range[1]))]

        # Tabs
        dashboard_tab, anomaly_tab, forecast_tab, insights_tab, rawdata_tab = st.tabs(
            ["📊 Dashboard", "🚨 Anomalies", "📈 Forecast", "🤖 Insights", "📂 Raw Data"]
        )

        with dashboard_tab:
            st.subheader("📊 Financial Overview")
            # Use corrected KPI computation
            income, expenses, savings, savings_rate = compute_kpis(df)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"<div class='metric-card'><div class='metric-value'>€{income:,.2f}</div><div class='metric-label'>Avg Monthly Income</div></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='metric-card'><div class='metric-value'>€{expenses:,.2f}</div><div class='metric-label'>Expenses</div></div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='metric-card'><div class='metric-value'>€{savings:,.2f}</div><div class='metric-label'>Savings</div></div>", unsafe_allow_html=True)
            col4.markdown(f"<div class='metric-card'><div class='metric-value'>{savings_rate:.1f}%</div><div class='metric-label'>Savings Rate</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                plot_category_spending(df)
            with col2:
                plot_monthly_trends(df)

        with anomaly_tab:
            st.subheader("🚨 Anomaly Detection")
            show_anomalies(df)

        with forecast_tab:
            st.subheader("📈 Forecasting (Trend + Moving Average)")
            forecast_expenses(df)

        with insights_tab:
            st.subheader("🤖 Spending Behavior Insights")
            spending_clusters(df)

        with rawdata_tab:
            st.subheader("📂 Raw Transactions")
            st.dataframe(df)
            st.download_button("💾 Download Processed CSV", df.to_csv(index=False), "processed_transactions.csv")

    else:
        st.warning("👆 Upload a CSV or enter your transactions to begin.")


if __name__ == "__main__":
    main()
