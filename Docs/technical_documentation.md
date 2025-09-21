# Finance Intelligence Dashboard – Technical Documentation

This document provides a **technical overview** of the Finance Intelligence Dashboard, explaining each feature page, ML/analytics techniques used, and key implementation details.

---

## Architecture Overview

The dashboard follows a **modular pipeline**:

1. **Data Input & Preprocessing**
   - Load CSV or default sample data.
   - Parse `Date` column and extract `Month`.
   - Clean and normalize `Category` labels.

2. **Analytics Module**
   - Compute financial KPIs: Income, Expenses, Savings, Savings Rate.
   - Detect anomalies and forecast trends.
   - Cluster monthly spending for insights.

3. **Visualization Module**
   - Streamlit-based interactive dashboard.
   - Tabs for overview, analytics, insights, and raw data.
   - Dynamic charts and KPI cards.

---

## Feature Pages

### 1. Dashboard Tab
**Purpose:** High-level overview of finances.

**Components:**
- KPI cards: Income, Expenses, Savings, Savings Rate.
- Category Spending chart: Total per category.
- Monthly Trends chart: Line chart of spending/income over months.

**Technical Details:**
- KPIs computed by aggregating monthly sums.
- Charts generated using **Plotly** or Streamlit built-in chart components.

---

### 2. Monthly Expenses Tab
**Purpose:** Detailed breakdown of monthly spending.

**Components:**
- Table of monthly expenses per category.
- Stacked bar charts showing income vs expense by month.

**Technical Details:**
- Uses `pandas.groupby("Month")` to summarize data.
- Visualizes trends to help identify high spending periods.

---

### 3. Anomalies Tab
**Purpose:** Detect unusual transactions.

**ML/Analytics Techniques:**
- **Z-score method**: Flags transactions that deviate significantly from the mean.  
- Optionally: **Isolation Forest** or **Local Outlier Factor** for larger datasets.

**Components:**
- Table highlighting anomalous transactions.
- Color-coded alerts for easy identification.

---

### 4. Forecasting Tab
**Purpose:** Predict future monthly expenses.

**Data Preprocessing:**
- Select negative `Amount` values (expenses) and convert to positive.
- Aggregate expenses monthly using `pandas.groupby`.
- Require at least 6 months of data for reliable forecasting.

**Forecasting Model:**
- **SARIMAX** (Seasonal ARIMA) from `statsmodels`.
- Parameters:
  - ARIMA order `(1,1,1)` → trend, differencing, short-term autoregression.
  - Seasonal order `(1,1,1,12)` → yearly seasonality.

**Outputs:**
- Forecasted monthly expenses for next `forecast_months` (default 6).
- Confidence intervals (`Lower_CI` and `Upper_CI`) for uncertainty estimation.
- Returns a DataFrame with columns: `Month`, `Predicted_Expense`, `Lower_CI`, `Upper_CI`.

**Visualization:**
- Plotly chart with:
  - Actual monthly expenses (bar chart)
  - Forecasted expenses (dashed line)
  - Shaded confidence interval

---

### 5. Insights Tab
**Purpose:** Cluster-based analysis of spending behavior.

**ML/Analytics Techniques:**
- **K-Means Clustering**: Groups months based on total spending.
- Quartiles (`q1`, `q2`) used to label clusters as **Low, Medium, High** spending months.

**Components:**
- Month labels with colored dots (red = high, green = low, etc.).
- Summary table of cluster statistics.
- Helps users identify patterns and optimize spending.

---

### 6. Raw Data Tab
**Purpose:** Access all uploaded transaction data.

**Components:**
- Interactive table using **Streamlit DataFrame**.
- Search, sort, and filter transactions.
- Useful for audit and verification purposes.

**Technical Details:**
- Directly displays the preprocessed DataFrame.
- Supports pagination for large datasets.

---

## KPIs Computation

| KPI             | Description |
|-----------------|-------------|
| Income          | Sum of monthly salary transactions. |
| Expenses        | Sum of absolute values of negative transactions. |
| Savings         | Income − Expenses. |
| Savings Rate    | `(Savings / Income) * 100` |

---

## ML / Analytics Summary

| Feature Page | Technique Used |
|--------------|----------------|
| Anomalies Tab | Z-score, Isolation Forest (optional) |
| Forecasting Tab | SARIMAX (Seasonal ARIMA) |
| Insights Tab | K-Means Clustering, Quartiles |

---

## Technical Stack

- **Python 3.10+**
- **Pandas** – Data loading and preprocessing
- **NumPy** – Numerical computations
- **Scikit-learn** – Clustering (K-Means), optional anomaly detection
- **Statsmodels** – Forecasting (SARIMAX)
- **Streamlit** – Dashboard UI
- **Plotly / Matplotlib** – Charts and plots

---

## Notes

- All ML/analytics run on **monthly aggregated data** to reduce noise.
- Dashboard is **interactive**, updates immediately on CSV upload.
- Future improvements:
  - Multi-currency support
  - Advanced anomaly detection (Isolation Forest, LOF)
  - Export insights to Excel or PDF
