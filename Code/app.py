import streamlit as st
import pandas as pd
from utils import load_data, preprocess_data, compute_kpis
from visualize import plot_category_spending, plot_monthly_trends, show_anomalies, forecast_expenses, spending_clusters, plot_monthly_expenses
import os
import altair as alt
import base64

def main():
    st.set_page_config(page_title="Finance Intelligence Dashboard", layout="wide")

    # ---------------- Background Video ----------------
    video_path = "../Sample_Data/bg.mp4"
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode()

        st.markdown(f"""
        <style>
        #bg-video {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: -1;
            opacity: 0.15;
        }}
        .stApp {{ background: transparent !important; }}
        .metric-card {{ background-color: rgba(255,255,255,0.65) !important; }}
        h1,h2,h3,h4,h5,h6,div[data-testid="stMarkdownContainer"] {{
            background-color: rgba(255,255,255,0) !important;
        }}
        .stCheckbox, .stMultiSelect, .stNumberInput, .stButton {{
            background-color: rgba(255,255,255,0.85) !important;
        }}
        </style>

        <video id="bg-video" autoplay muted loop playsinline>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>
        """, unsafe_allow_html=True)

    # ---------------- Font Awesome + CSS ----------------
    st.markdown("""
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
        .metric-card {
            padding: 15px; border-radius: 15px;
            background: rgba(255,255,255,0.5);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            text-align: center; margin-bottom: 10px;
        }
        .metric-value { font-size: 26px; font-weight: bold; color: #1E88E5; }
        .metric-label { font-size: 14px; color: gray; display: flex; align-items: center; justify-content: center; gap: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center;'>💰 Finance Intelligence Dashboard</h2>", unsafe_allow_html=True)

    # ---------------- CSV Upload / Default ----------------
    uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])
    use_default = st.checkbox("Use default CSV")

    # Clear df if neither uploaded nor default selected
    if not uploaded_file and not use_default:
        if 'df' in st.session_state:
            del st.session_state['df']

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

    if 'df' in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df

        # Sidebar filters
        st.sidebar.markdown('<h3><i class="fa-solid fa-gear"></i> Filters</h3>', unsafe_allow_html=True)
        categories = st.sidebar.multiselect("Filter by Category", df["Category"].unique(), default=df["Category"].unique())
        df_filtered = df[df["Category"].isin(categories)]
        income_categories = ['salary']

        # Tabs
        dashboard_tab, monthly_tab, anomaly_tab, forecast_tab, insights_tab, rawdata_tab = st.tabs(
            ["Dashboard", "Monthly Expenses", "Anomalies", "Forecast", "Insights", "Raw Data"]
        )

        # ---------------- Dashboard Tab ----------------
        with dashboard_tab:
            st.markdown('<h3><i class="fa-solid fa-chart-pie"></i> Financial Overview</h3>', unsafe_allow_html=True)
            income, expenses, savings, savings_rate = compute_kpis(df_filtered)
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"<div class='metric-card'><div class='metric-value'>€{income:,.2f}</div><div class='metric-label'><i class='fa-solid fa-wallet'></i> Avg Monthly Income</div></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='metric-card'><div class='metric-value'>€{expenses:,.2f}</div><div class='metric-label'><i class='fa-solid fa-credit-card'></i> Expenses</div></div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='metric-card'><div class='metric-value'>€{savings:,.2f}</div><div class='metric-label'><i class='fa-solid fa-piggy-bank'></i> Savings</div></div>", unsafe_allow_html=True)
            col4.markdown(f"<div class='metric-card'><div class='metric-value'>{savings_rate:.1f}%</div><div class='metric-label'><i class='fa-solid fa-percentage'></i> Savings Rate</div></div>", unsafe_allow_html=True)

            st.markdown('---')
            col1, col2 = st.columns(2)
            with col1:
                plot_category_spending(df_filtered)
            with col2:
                plot_monthly_trends(df_filtered)

        # ---------------- Monthly Expenses Tab ----------------
        with monthly_tab:
            plot_monthly_expenses(df_filtered, income_categories=income_categories)

        # ---------------- Anomalies Tab ----------------
        with anomaly_tab:
            st.markdown('<h3><i class="fa-solid fa-triangle-exclamation"></i> Anomaly Detection</h3>', unsafe_allow_html=True)
            show_anomalies(df_filtered)

        # ---------------- Forecast Tab ----------------
        with forecast_tab:
            st.markdown('<h3><i class="fa-solid fa-chart-line"></i> Forecasting</h3>', unsafe_allow_html=True)
            forecast_expenses(df_filtered)

        # ---------------- Insights Tab ----------------
        with insights_tab:
            st.markdown('<h3><i class="fa-solid fa-robot"></i> Spending Insights</h3>', unsafe_allow_html=True)
            spending_clusters(df_filtered)

        # ---------------- Raw Data Tab ----------------
        with rawdata_tab:
            st.markdown('<h3><i class="fa-solid fa-folder-open"></i> Raw Data</h3>', unsafe_allow_html=True)
            st.dataframe(df_filtered)

        # ---------------- Video Credits ----------------
        st.markdown("""
        <div style="text-align:center; font-size:12px; color:gray; margin-top:20px;">
            Background video: <a href="https://www.vecteezy.com/free-videos/background" target="_blank">Vecteezy Free Background Videos</a>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Upload a CSV or select default CSV to view the dashboard.")


if __name__ == "__main__":
    main()
