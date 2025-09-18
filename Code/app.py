import streamlit as st
import pandas as pd
from utils import load_data, preprocess_data, compute_kpis
from visualize import plot_category_spending, plot_monthly_trends, show_anomalies, forecast_expenses, spending_clusters
import os

def main():
    st.set_page_config(page_title="Finance Intelligence Dashboard", layout="wide")

    # Load Font Awesome
    st.markdown("""
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
        .main { background-color: #f4f6f9; }
        .metric-card {
            padding: 15px; border-radius: 15px; background: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center;
            margin-bottom: 10px;
        }
        .metric-value { font-size: 26px; font-weight: bold; color: #1E88E5; }
        .metric-label { font-size: 14px; color: gray; display: flex; align-items: center; justify-content: center; gap: 5px; }
        </style>
    """, unsafe_allow_html=True)

    # ---------------- Landing Page / CSV Loading ----------------
    st.markdown("<h2 style='text-align:center;'>💰 Finance Intelligence Dashboard</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload your own CSV", type=["csv"], key="upload_csv")
    use_default = st.checkbox("Use default CSV instead of uploading", key="use_default_csv")

    # Auto-clear session state if toggle is unchecked
    if 'df' in st.session_state and not (uploaded_file or use_default):
        del st.session_state.df

    df = None
    if uploaded_file:
        df = load_data(uploaded_file)
    elif use_default:
        default_path = os.path.join("../Sample_Data", "default_transactions.csv")
        if os.path.exists(default_path):
            df = load_data(default_path)
        else:
            st.error("Default CSV not found.")

    if df is not None:
        st.session_state.df = df

    # ---------------- Main Dashboard / Analytics ----------------
    if 'df' in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df

        

        # Sidebar Filters
        st.sidebar.markdown('<h3><i class="fa-solid fa-gear"></i> Filters</h3>', unsafe_allow_html=True)
        categories = st.sidebar.multiselect(
            "Filter by Category", df["Category"].unique(), default=df["Category"].unique()
        )
        df_filtered = df[df["Category"].isin(categories)]

        # Tabs
        dashboard_tab, anomaly_tab, forecast_tab, insights_tab, rawdata_tab = st.tabs(
            ["Dashboard", "Anomalies", "Forecast", "Insights", "Raw Data"]
        )

        # ---------------- Dashboard Tab ----------------
        with dashboard_tab:
            st.markdown('<h3><i class="fa-solid fa-chart-pie"></i> Financial Overview</h3>', unsafe_allow_html=True)
            income, expenses, savings, savings_rate = compute_kpis(df_filtered)

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>€{income:,.2f}</div>
                <div class='metric-label'><i class="fa-solid fa-wallet"></i> Avg Monthly Income</div>
            </div>""", unsafe_allow_html=True)

            col2.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>€{expenses:,.2f}</div>
                <div class='metric-label'><i class="fa-solid fa-credit-card"></i> Expenses</div>
            </div>""", unsafe_allow_html=True)

            col3.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>€{savings:,.2f}</div>
                <div class='metric-label'><i class="fa-solid fa-piggy-bank"></i> Savings</div>
            </div>""", unsafe_allow_html=True)

            col4.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{savings_rate:.1f}%</div>
                <div class='metric-label'><i class="fa-solid fa-percentage"></i> Savings Rate</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                plot_category_spending(df_filtered)
            with col2:
                plot_monthly_trends(df_filtered)

        # ---------------- Anomaly Tab ----------------
        with anomaly_tab:
            st.markdown('<h3><i class="fa-solid fa-triangle-exclamation"></i> Anomaly Detection</h3>', unsafe_allow_html=True)
            show_anomalies(df_filtered)

        # ---------------- Forecast Tab ----------------
        with forecast_tab:
            st.markdown('<h3><i class="fa-solid fa-chart-line"></i> Forecasting (Monthly Expenses)</h3>', unsafe_allow_html=True)
            forecast_expenses(df_filtered)

        # ---------------- Insights Tab ----------------
        with insights_tab:
            st.markdown('<h3><i class="fa-solid fa-robot"></i> Spending Behavior Insights</h3>', unsafe_allow_html=True)
            spending_clusters(df_filtered)

        # ---------------- Raw Data Tab ----------------
        with rawdata_tab:
            st.markdown('<h3><i class="fa-solid fa-folder-open"></i> Raw Transactions</h3>', unsafe_allow_html=True)
            st.dataframe(df_filtered)
            
    else:
        st.info("Upload a CSV or select the default CSV to view the dashboard.")

if __name__ == "__main__":
    main()
