import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Import existing modules
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from financial_analyzer import FinancialAnalyzer
from Operational_Efficiency import OperationalAnalyzer
from driver_analyzer import DriverPerformanceAnalyzer
from fuel_maintenance import FuelMaintenanceAnalyzer
from Visualization import PredictiveInsights, AdvancedVisualizer

# Page Config
st.set_page_config(
    page_title="FleetSmart Analytics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Metric Cards - Dark Theme Styling */
    div[data-testid="stMetric"], .stMetric {
        background-color: #262730 !important; /* Streamlit Dark Gray */
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #464b5f;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Ensure text visibility in dark cards (Streamlit usually handles this, but we force it just in case) */
    div[data-testid="stMetricLabel"] > label {
        color: #fafafa !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
    }
    
    /* Headings coloring for Dark Mode */
    h1, h2, h3 {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading (Cached) ---
@st.cache_resource
def load_data():
    engine = DataEngine()  # Uses default "Data files" folder
    preprocessor = DataPreprocessor(engine)
    data = preprocessor.run_pipeline()
    return data

try:
    with st.spinner('Loading and analyzing fleet data...'):
        data = load_data()
    
    if not data:
        st.error("Failed to load data. Please check your 'data files/' directory.")
        st.stop()
        
except Exception as e:
    st.error(f"An error occurred during data loading: {e}")
    st.stop()

# --- Helpers ---
def format_currency(value):
    return f"${value:,.0f}"

def format_pct(value):
    return f"{value:.1f}%"

# --- Sidebar Navigation ---
st.sidebar.title("🚚 FleetSmart")
st.sidebar.markdown("### Logistics Analytics Dashboard")
page = st.sidebar.radio("Navigate to:", 
    ["Financial Performance", 
     "Operational Efficiency", 
     "Driver Performance", 
     "Fuel & Maintenance",
     "Predictive Insights"])

st.sidebar.markdown("---")
st.sidebar.info("v1.0.0 | Streamlit Edition")

# --- Page: Financial Performance ---
if page == "Financial Performance":
    st.title("💰 Financial Performance Dashboard")
    
    analyzer = FinancialAnalyzer(data)
    df = analyzer.df  # Access prepared dataframe
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    total_rev = df['revenue'].sum()
    total_profit = df['profit'].sum()
    margin = (total_profit / total_rev * 100) if total_rev else 0
    total_miles = df['actual_distance_miles'].sum()
    
    col1.metric("Total Revenue", format_currency(total_rev))
    col2.metric("Total Profit", format_currency(total_profit), f"{margin:.1f}% Margin")
    col3.metric("Profit Margin", f"{margin:.1f}%")
    col4.metric("Total Miles", f"{total_miles:,.0f}")
    
    st.markdown("---")
    
    # Monthly Trends
    st.subheader("Monthly Financial Trends")
    fig = analyzer.plot_monthly_trends()
    if fig: st.pyplot(fig)
    
    # Route Profitability
    st.subheader("Route Profitability Analysis")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("#### Top 5 Most Profitable Routes")
        fig = analyzer.plot_route_profitability()
        if fig: st.pyplot(fig)
        
    with col_r:
        st.markdown("#### Profitability Distribution (Risk)")
        fig_dist = analyzer.plot_profit_distribution()
        if fig_dist: st.pyplot(fig_dist)

# --- Page: Operational Efficiency ---
elif page == "Operational Efficiency":
    st.title("⏱️ Operational Efficiency Dashboard")
    
    analyzer = OperationalAnalyzer(data)
    df = analyzer.op_data
    
    if df.empty:
        st.warning("No operational data available.")
    else:
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        on_time_rate = df['on_time'].mean() * 100
        fleet_util = df['utilization_rate'].mean() * 100 if 'utilization_rate' in df.columns else 0
        avg_idle = df['average_idle_hours'].mean() if 'average_idle_hours' in df.columns else 0
        
        col1.metric("On-Time Delivery", format_pct(on_time_rate), delta_color="normal" if on_time_rate > 90 else "inverse")
        col2.metric("Fleet Utilization", format_pct(fleet_util))
        col3.metric("Avg Idle Hours", f"{avg_idle:.1f} hrs")
        col4.metric("Active Trips", f"{len(df):,}")
        
        st.markdown("---")
        
        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("On-Time vs Delayed")
            fig = analyzer.plot_ontime_distribution()
            if fig: st.pyplot(fig)
            
        with c2:
            st.subheader("Monthly On-Time Reliability")
            fig = analyzer.plot_ontime_trend()
            if fig: st.pyplot(fig)

# --- Page: Driver Performance ---
elif page == "Driver Performance":
    st.title("👨‍✈️ Driver Performance Leaderboard")
    
    analyzer = DriverPerformanceAnalyzer(data)
    # Using logic similar to show_dashboard but returning df
    
    drivers = data.get('drivers')
    driver_monthly = data.get('driver_monthly_metrics')
    
    if driver_monthly is not None and not driver_monthly.empty:
        df_drv = driver_monthly.copy()
        
        # Merge names
        if drivers is not None:
            df_drv = df_drv.merge(drivers[['driver_id', 'first_name', 'last_name']], on='driver_id', how='left')
            df_drv['Driver Name'] = df_drv['first_name'].fillna('') + " " + df_drv['last_name'].fillna('')
        else:
            df_drv['Driver Name'] = "Driver " + df_drv['driver_id'].astype(str)
            
        # Metrics
        numeric_cols = ['total_revenue', 'average_mpg', 'on_time_delivery_rate', 'average_idle_hours']
        for col in numeric_cols:
             if col in df_drv.columns:
                df_drv[col] = pd.to_numeric(df_drv[col], errors='coerce').fillna(0)
        
        # Aggregate by driver (if multiple months exist)
        leaderboard = df_drv.groupby(['driver_id', 'Driver Name']).agg({
            'total_revenue': 'sum',
            'average_mpg': 'mean',
            'on_time_delivery_rate': 'mean',
            'average_idle_hours': 'mean'
        }).reset_index()
        
        # Scoring
        leaderboard['Score'] = (
            (leaderboard['total_revenue'] / 1000 * 0.5) + 
            (leaderboard['average_mpg'] * 4) + 
            (leaderboard['on_time_delivery_rate'] * 100 * 0.4) - 
            (leaderboard['average_idle_hours'] * 3)
        )
        
        leaderboard = leaderboard.sort_values('Score', ascending=False)
        
        # Display Top 10
        st.subheader("🏆 Top 10 Drivers")
        st.dataframe(
            leaderboard[['Driver Name', 'Score', 'total_revenue', 'average_mpg', 'on_time_delivery_rate', 'average_idle_hours']]
            .rename(columns={
                'total_revenue': 'Revenue ($)', 
                'average_mpg': 'MPG', 
                'on_time_delivery_rate': 'On-Time Rate',
                'average_idle_hours': 'Idle Hrs'
            })
            .head(10)
            .style.format({
                'Score': '{:.1f}',
                'Revenue ($)': '${:,.0f}',
                'MPG': '{:.1f}',
                'On-Time Rate': '{:.1%}',
                'Idle Hrs': '{:.1f}'
            }),
            use_container_width=True
        )
        
        # Enhanced Performance Matrix
        st.subheader("🚀 Performance Matrix: Efficiency vs Revenue")
        fig = analyzer.plot_performance_matrix()
        if fig: st.pyplot(fig)
        
        # [Integrated] Safety Heatmap
        st.markdown("---")
        st.subheader("Safety vs. Efficiency Correlation")
        fig_safe = analyzer.plot_safety_heatmap()
        if fig_safe: st.pyplot(fig_safe)

# --- Page: Fuel & Maintenance ---
elif page == "Fuel & Maintenance":
    st.title("⛽ Fuel & Maintenance Analytics")
    
    fuel_analyzer = FuelMaintenanceAnalyzer(data)
    fuel = data.get('fuel_purchases')
    maint = data.get('maintenance_records')
    
    if fuel is not None and maint is not None:
        col1, col2 = st.columns(2)
        
        # Summary Metrics
        with col1:
            st.subheader("Fuel Overview")
            st.metric("Total Fuel Cost", format_currency(fuel['total_cost'].sum()))
            st.metric("Total Gallons", f"{fuel['gallons'].sum():,.0f}")
            st.metric("Avg Price/Gallon", f"${fuel['price_per_gallon'].mean():.2f}")
            
        with col2:
            st.subheader("Maintenance Overview")
            st.metric("Total Maintenance Cost", format_currency(maint['total_cost'].sum()))
            st.metric("Maintenance Events", f"{len(maint):,}")
            st.metric("Avg Downtime", f"{maint['downtime_hours'].mean():.1f} hrs")
            
        st.markdown("---")
        
        # Top 5 Expensive Trucks
        st.subheader("🚛 Highest Cost Trucks (Fuel + Maintenance)")
        fig = fuel_analyzer.plot_cost_distribution()
        if fig: st.pyplot(fig)

# --- Page: Predictive Insights ---
elif page == "Predictive Insights":
    st.title("📈 Analytical Insights & Patterns")
    st.info("Advanced analytics based on historical data patterns and rule-based logic.")
    
    ins = PredictiveInsights(data)
    vis = AdvancedVisualizer(data)
    fuel_analyzer = FuelMaintenanceAnalyzer(data) # Initialize this!
    
    tab1, tab2, tab3 = st.tabs(["📊 Growth & Volume", "⚠️ Maintenance Risk", "📅 Seasonal Patterns"])
    
    with tab1:
        st.header("Historical Growth Analysis")
        # Logic from Page 1 (simplified directly to charts)
        loads = data.get('loads').copy()
        loads['load_date'] = pd.to_datetime(loads['load_date'], errors='coerce')
        loads['month'] = loads['load_date'].dt.to_period('M')
        monthly_loads = loads.groupby('month').size().sort_index()
        
        col1, col2 = st.columns(2)
        with col1:
             st.subheader("Monthly Load Volume")
             st.bar_chart(monthly_loads)
        
        with col2:
             st.subheader("Growth Rate Trend")
             growth = monthly_loads.pct_change().fillna(0) * 100
             st.line_chart(growth)
             
    with tab2:
        st.header("Fleet Maintenance Risk Radar")
        st.markdown("Identifies high-risk vehicles based on **Mileage** and **Age** thresholds.")
        
        # Use robust Fuel Analyzer method
        fig = fuel_analyzer.plot_maintenance_risk()
        if fig: st.pyplot(fig)
        
    with tab3:
        st.header("Peak Seasonality Heatmap")
        st.markdown("Visualizes load density by **Month** and **Day of Week**.")
        fig = vis.seasonality_heatmap()
        if fig: st.pyplot(fig)