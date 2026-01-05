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
from Visualization import PredictiveInsights

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
    /* Force light background for the main area to match the hardcoded styling */
    .stApp {
        background-color: #f8f9fa;
        color: #000000;
    }
    
    /* Style the metric cards */
    div[data-testid="stMetric"], .stMetric {
        background-color: #ffffff !important;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    
    /* Force text colors inside metrics to be black for visibility */
    div[data-testid="stMetricLabel"] > label {
        color: #444444 !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #000000 !important;
    }
    div[data-testid="stMetricDelta"] > div {
        /* Start with inheriting, but usually delta handles its own color (green/red) */
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
    }
    
    /* General text */
    p, li, span {
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading (Cached) ---
@st.cache_resource
def load_data():
    engine = DataEngine("data files/")
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
    m = df.copy()
    m['month'] = m['load_date'].dt.to_period('M').astype(str)
    monthly = m.groupby('month')[['revenue', 'profit']].sum()
    
    st.bar_chart(monthly)
    
    # Route Profitability
    st.subheader("Route Profitability Analysis")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("#### Top 5 Most Profitable Routes")
        route_stats = df.groupby('route_name').agg({'profit': 'sum', 'revenue': 'sum', 'load_id': 'count'})
        route_stats = route_stats[route_stats['load_id'] >= 5]
        route_stats['margin'] = (route_stats['profit'] / route_stats['revenue'] * 100)
        top_routes = route_stats.nlargest(5, 'margin')
        st.dataframe(top_routes[['margin', 'profit']], use_container_width=True)
        
    with col_r:
        st.markdown("#### Least Profitable Routes")
        bottom_routes = route_stats.nsmallest(5, 'margin')
        st.dataframe(bottom_routes[['margin', 'profit']], use_container_width=True)

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
            otd_counts = df['on_time'].value_counts().rename({True: 'On-Time', False: 'Delayed'})
            fig, ax = plt.subplots()
            ax.pie(otd_counts, labels=otd_counts.index, autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'], startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
            
        with c2:
            st.subheader("Monthly On-Time Reliability")
            if 'dispatch_date' in df.columns:
                m_otd = df.copy()
                m_otd['month'] = m_otd['dispatch_date'].dt.to_period('M').astype(str)
                trend = m_otd.groupby('month')['on_time'].mean() * 100
                st.line_chart(trend)

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
        
        # Scatter Plot
        st.subheader("Performance Matrix: Revenue vs MPG")
        chart_data = leaderboard[['total_revenue', 'average_mpg', 'Driver Name']]
        st.scatter_chart(
            chart_data,
            x='average_mpg',
            y='total_revenue',
            color='Driver Name',
            size=100
        )

# --- Page: Fuel & Maintenance ---
elif page == "Fuel & Maintenance":
    st.title("⛽ Fuel & Maintenance Analytics")
    
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
        
        fuel_cost = fuel.groupby('truck_id')['total_cost'].sum()
        maint_cost = maint.groupby('truck_id')['total_cost'].sum()
        
        total_cost = pd.DataFrame({'Fuel': fuel_cost, 'Maintenance': maint_cost}).fillna(0)
        total_cost['Total'] = total_cost['Fuel'] + total_cost['Maintenance']
        
        top_trucks = total_cost.nlargest(5, 'Total')
        
        st.bar_chart(top_trucks[['Fuel', 'Maintenance']])

# --- Page: Predictive Insights ---
elif page == "Predictive Insights":
    st.title("📈 Predictive Insights & Forecasts")
    
    ins = PredictiveInsights(data)
    
    # We will reuse the logic from PredictiveInsights but capture the figures
    # Page 1 logic
    st.header("Demand Analysis")
    fig1, gs1 = ins.create_page(1, "Demand & Demand Volume")
    
    loads = data.get('loads').copy()
    loads['load_date'] = pd.to_datetime(loads['load_date'], errors='coerce')
    loads['month'] = loads['load_date'].dt.to_period('M')
    monthly_loads = loads.groupby('month').size().sort_index()
    
    # Re-impl plotting on the figure
    ax1 = fig1.add_subplot(gs1[0, 0])
    last_12 = monthly_loads.tail(12)
    last_12.plot(kind='bar', ax=ax1, color='#3498db')
    ax1.set_title('Monthly Load Volume (Last 12 Months)')
    
    ax2 = fig1.add_subplot(gs1[0, 1])
    monthly_loads.plot(linewidth=3, marker='o', ax=ax2, color='#2ecc71')
    ax2.set_title('Load Volume Trend')
    
    ax3 = fig1.add_subplot(gs1[1, :])
    growth = monthly_loads.pct_change().fillna(0) * 100
    growth.plot(kind='bar', ax=ax3, color=np.where(growth > 0, 'green', 'red'))
    ax3.set_title('Monthly Growth Rate (%)')
    
    st.pyplot(fig1)
    
    st.markdown("---")
    
    st.header("Cost Efficiency")
    fig2, gs2 = ins.create_page(2, "Maintenance & Fuel")
    
    # Just a sample of the second page to show capability
    maint = data.get('maintenance_records')
    ax1 = fig2.add_subplot(gs2[0, 0])
    if maint is not None:
        maint.groupby('truck_id').size().sort_values(ascending=False).head(10).plot(kind='barh', ax=ax1, color='#e74c3c')
        ax1.set_title('Top Trucks by Maintenance Freq')
        
    fuel = data.get('fuel_purchases')
    ax2 = fig2.add_subplot(gs2[0, 1])
    if fuel is not None:
        fuel['purchase_date'] = pd.to_datetime(fuel['purchase_date'], errors='coerce')
        monthly_fuel = fuel.groupby(fuel['purchase_date'].dt.to_period('M'))['total_cost'].sum()
        monthly_fuel.plot(ax=ax2, color='#f39c12')
        ax2.set_title('Monthly Fuel Cost')
        
    st.pyplot(fig2)

