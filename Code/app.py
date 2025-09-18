import streamlit as st
import pandas as pd
from utils import load_data, preprocess_data, compute_kpis
from visualize import plot_category_spending, plot_monthly_trends, show_anomalies, forecast_expenses, spending_clusters


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
        df = st.data_editor(pd.DataFrame(columns=["Date","Description","Category","Amount"]), num_rows="dynamic")
        if not df.empty:
            df = preprocess_data(df)

    if df is not None and not df.empty:
        # Sidebar Filters
        categories = st.sidebar.multiselect(
            "Filter by Category", df["Category"].unique(), default=df["Category"].unique()
        )
        df = df[df["Category"].isin(categories)]

        # Tabs
        dashboard_tab, anomaly_tab, forecast_tab, insights_tab, rawdata_tab = st.tabs(
            ["📊 Dashboard", "🚨 Anomalies", "📈 Forecast", "🤖 Insights", "📂 Raw Data"]
        )

        with dashboard_tab:
            st.subheader("📊 Financial Overview")
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
            st.subheader("📈 Forecasting (Monthly Expenses)")
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
