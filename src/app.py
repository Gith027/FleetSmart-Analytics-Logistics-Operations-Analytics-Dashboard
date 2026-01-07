"""
FleetSmart Analytics Dashboard - Professional Streamlit UI
Complete redesign with filtering, export, and all backend features
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime, timedelta
from contextlib import contextmanager

# Import backend modules
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from financial_analyzer import FinancialAnalyzer
from Operational_Efficiency import OperationalAnalyzer
from driver_analyzer import DriverPerformanceAnalyzer
from fuel_maintenance import FuelMaintenanceAnalyzer
from Visualization import PredictiveInsights, AdvancedVisualizer
from alerts_engine import AlertsEngine, AlertThresholdConfig

# ============== PAGE CONFIG ==============
st.set_page_config(
    page_title="FleetSmart Analytics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CUSTOM CSS ==============
def load_custom_css():
    # Check theme preference
    dark_mode = st.session_state.get('dark_mode', True)
    
    if dark_mode:
        css = """
        <style>
            /* Dark Theme Professional Styling */
            :root {
                --primary: #4F46E5;
                --success: #10B981;
                --warning: #F59E0B;
                --danger: #EF4444;
                --bg-dark: #0F172A;
                --card-bg: #1E293B;
                --text: #F8FAFC;
            }
            
            /* Main Background */
            .stApp {
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            }
            
            /* Metric Cards - Glassmorphism */
            div[data-testid="stMetric"] {
                background: rgba(30, 41, 59, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            div[data-testid="stMetricLabel"] > label {
                color: #94A3B8 !important;
                font-size: 0.9rem;
            }
            
            div[data-testid="stMetricValue"] > div {
                color: #F8FAFC !important;
                font-weight: 600;
            }
            
            /* Headings */
            h1, h2, h3 {
                color: #F8FAFC !important;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                transition: all 0.3s ease;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
            }
            
            /* DataFrames */
            .stDataFrame {
                border-radius: 12px;
                overflow: hidden;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: rgba(30, 41, 59, 0.5);
                border-radius: 8px;
                padding: 8px 16px;
            }
            
            /* Alert boxes */
            .alert-critical {
                background: rgba(239, 68, 68, 0.2);
                border-left: 4px solid #EF4444;
                padding: 12px;
                border-radius: 8px;
                margin: 8px 0;
            }
            
            .alert-warning {
                background: rgba(245, 158, 11, 0.2);
                border-left: 4px solid #F59E0B;
                padding: 12px;
                border-radius: 8px;
                margin: 8px 0;
            }
            
            .alert-info {
                background: rgba(16, 185, 129, 0.2);
                border-left: 4px solid #10B981;
                padding: 12px;
                border-radius: 8px;
                margin: 8px 0;
            }
            
            /* Smooth transitions */
            * {
                transition: background-color 0.2s ease, color 0.2s ease;
            }
        </style>
        """
    else:
        css = """
        <style>
            /* Light Theme */
            .stApp {
                background: #F8FAFC;
            }
            
            div[data-testid="stMetric"] {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }
            
            div[data-testid="stMetricLabel"] > label {
                color: #64748B !important;
            }
            
            div[data-testid="stMetricValue"] > div {
                color: #1E293B !important;
            }
            
            h1, h2, h3 {
                color: #1E293B !important;
            }
            
            section[data-testid="stSidebar"] {
                background: white;
                border-right: 1px solid #E2E8F0;
            }
        </style>
        """
    
    st.markdown(css, unsafe_allow_html=True)

# ============== DATA LOADING ==============
@st.cache_resource
def load_data():
    """Load and preprocess all data with caching"""
    engine = DataEngine()
    preprocessor = DataPreprocessor(engine)
    data = preprocessor.run_pipeline()
    return data

# ============== HELPER FUNCTIONS ==============
def format_currency(value):
    """Format number as currency"""
    if pd.isna(value) or value is None:
        return "$0"
    return f"${value:,.0f}"

def format_pct(value):
    """Format number as percentage"""
    if pd.isna(value) or value is None:
        return "0.0%"
    return f"{value:.1f}%"

def format_compact_number(value):
    """Format large numbers with suffixes (K, M, B)"""
    if pd.isna(value) or value is None:
        return "0"
    if not isinstance(value, (int, float)):
        return str(value)
    
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif abs_value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:.0f}"

def export_to_csv(df, filename):
    """Generate CSV download button"""
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Export CSV",
        data=csv,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def export_to_excel(df, filename):
    """Generate Excel download button"""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    st.download_button(
        label="📥 Export Excel",
        data=buffer.getvalue(),
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@contextmanager
def loading_overlay():
    """Context manager for a custom full-screen loading overlay"""
    placeholder = st.empty()
    
    # CSS for the overlay (z-index 9999 ensures it's on top)
    overlay_html = """
    <style>
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(15, 23, 42, 0.85); /* Dark semi-transparent background */
            z-index: 9999;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            font-family: sans-serif;
        }
        .loading-spinner {
            border: 8px solid #f3f3f3;
            border-top: 8px solid #4F46E5; /* Primary color */
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1.5s linear infinite;
            margin-bottom: 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    <div class="loading-overlay">
        <div class="loading-spinner"></div>
        <h3>Loading details...</h3>
    </div>
    """
    
    placeholder.markdown(overlay_html, unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()

def display_ticker(alerts):
    """Display horizontal scrolling ticker for alerts"""
    if not alerts:
        return
    
    alert_items = []
    icon_map = {'critical': '🔴', 'warning': '🟡', 'info': '🟢'}
    
    for alert in alerts:
        icon = icon_map.get(alert.get('type'), '⚪')
        # Create a single line string for ticker
        item = f"{icon} <b>{alert.get('title')}</b>: {alert.get('message')} ({alert.get('metric', '')})"
        alert_items.append(f"<span style='display: inline-block; padding: 0 40px;'>{item}</span>")
    
    ticker_content = "".join(alert_items)
    
    # CSS for Marquee
    ticker_html = f"""
    <style>
        .ticker-wrap {{
            width: 100%;
            overflow: hidden;
            background-color: #1E293B;
            border-radius: 8px;
            padding: 10px 0;
            white-space: nowrap;
            box-sizing: border-box;
            border: 1px solid #334155;
            margin-top: 20px;
        }}
        .ticker {{
            display: inline-block;
            padding-left: 100%;
            animation: ticker 120s linear infinite;
        }}
        .ticker:hover {{
            animation-play-state: paused;
        }}
        @keyframes ticker {{
            0%   {{ transform: translate(0, 0); }}
            100% {{ transform: translate(-100%, 0); }}
        }}
    </style>
    <div class="ticker-wrap">
        <div class="ticker">
            {ticker_content}
        </div>
    </div>
    """
    st.markdown(ticker_html, unsafe_allow_html=True)

def display_alert(alert):
    """Display a single alert with styling"""
    icon = {'critical': '🔴', 'warning': '🟡', 'info': '🟢'}.get(alert.get('type'), '⚪')
    css_class = f"alert-{alert.get('type', 'info')}"
    
    st.markdown(f"""
    <div class="{css_class}">
        <strong>{icon} {alert.get('title', 'Alert')}</strong><br>
        <span style="color: #94A3B8;">{alert.get('message', '')}</span><br>
        <small><em>{alert.get('metric', '')}</em></small>
    </div>
    """, unsafe_allow_html=True)

def display_kpi_row(kpis, cols_config):
    """Display a row of KPI metric cards"""
    cols = st.columns(len(cols_config))
    for i, (key, label, formatter, delta) in enumerate(cols_config):
        value = kpis.get(key, 0)
        formatted = formatter(value) if callable(formatter) else f"{value}"
        cols[i].metric(label, formatted, delta if delta else None)

# ============== MAIN APPLICATION ==============
def main():
    # Initialize session state
    # Initialize session state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Overview"
    
    # Load CSS
    load_custom_css()
    
    # Load data
    try:
        with st.spinner('🚚 Loading FleetSmart Analytics...'):
            data = load_data()
        
        if not data:
            st.error("❌ Failed to load data. Please check your 'Data files/' directory.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.stop()
    
    # Initialize analyzers
    alerts_engine = AlertsEngine(data)
    alert_counts = alerts_engine.get_alert_count()
    
    # ============== SIDEBAR ==============
    with st.sidebar:
        st.markdown("# 🚚 FleetSmart")
        st.markdown("### Analytics Dashboard")
        st.markdown("---")
        
        # Navigation
        # Navigation
        pages = [
            "🏠 Overview",
            "💰 Financial Performance",
            "⏱️ Operational Efficiency",
            "👨‍✈️ Driver Performance",
            "⛽ Fleet Costs",
            "📈 Predictive Insights",
            f"⚠️ Alerts ({alert_counts['total']})",
            "⚙️ Settings",
            "ℹ️ Info"
        ]
        
        st.markdown("### Menu")
        for p in pages:
            if st.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
                st.session_state.page = p
                st.rerun()
        
        st.markdown("---")
        

    
    # ============== PAGE ROUTING ==============
    
    # ------- OVERVIEW PAGE -------
    # ------- OVERVIEW PAGE -------
    # ------- PAGE ROUTING WITH CUSTOM SPINNER -------
    with loading_overlay():
        # ------- OVERVIEW PAGE -------
        if st.session_state.page == "🏠 Overview":
            render_overview_page(data, alerts_engine)
        
        # ------- FINANCIAL PAGE -------
        elif st.session_state.page == "💰 Financial Performance":
            render_financial_page(data)
        
        # ------- OPERATIONAL PAGE -------
        elif st.session_state.page == "⏱️ Operational Efficiency":
            render_operational_page(data)
        
        # ------- DRIVER PAGE -------
        elif st.session_state.page == "👨‍✈️ Driver Performance":
            render_driver_page(data)
        
        # ------- FLEET COSTS PAGE -------
        elif st.session_state.page == "⛽ Fleet Costs":
            render_fleet_costs_page(data)
        
        # ------- PREDICTIVE INSIGHTS PAGE -------
        elif st.session_state.page == "📈 Predictive Insights":
            render_predictive_page(data)
        
        # ------- ALERTS PAGE -------
        elif st.session_state.page.startswith("⚠️ Alerts"):
            render_alerts_page(data, alerts_engine)
        
        # ------- SETTINGS PAGE -------
        elif st.session_state.page == "⚙️ Settings":
            render_settings_page()
        
        # ------- INFO PAGE -------
        elif st.session_state.page == "ℹ️ Info":
            render_info_page()


# ============== PAGE RENDERERS ==============

def render_overview_page(data, alerts_engine):
    """Render the Overview Dashboard page"""
    st.title("🏠 Fleet Operations Overview")
    st.markdown("Real-time summary of your entire fleet operations")
    st.markdown("---")
    # Summary KPIs from all modules
    col1, col2, col3= st.columns(3)
    
    # Financial KPIs
    fin_analyzer = FinancialAnalyzer(data)
    fin_kpis = fin_analyzer.get_kpis()
    col1.metric("💰 Total Revenue", format_compact_number(fin_kpis.get('total_revenue', 0)))
    col2.metric("📈 Profit Margin", format_pct(fin_kpis.get('profit_margin', 0)))
    
    # Operational KPIs
    ops_analyzer = OperationalAnalyzer(data)
    ops_kpis = ops_analyzer.get_kpis()
    col3.metric("⏱️ On-Time Rate", format_pct(ops_kpis.get('on_time_rate', 0)))
    
    
    
    st.markdown("---")
    # Horizontal Alerts Ticker
    st.markdown("### 🚨 Active Alerts")
    alerts = alerts_engine.get_all_alerts()
    if alerts:
        display_ticker(alerts[:10])  # Show top 10 in ticker
    else:
        st.success("✅ No active alerts - all systems normal!")
    
    # Full width chart
    st.subheader("📊 Monthly Performance Trend")
    fig = fin_analyzer.plot_monthly_trends()
    if fig:
        st.pyplot(fig)



def render_financial_page(data):
    """Render the Financial Performance page"""
    st.title("💰 Financial Performance Dashboard")
    
    analyzer = FinancialAnalyzer(data)
    
    # ===== FILTERS (Per-tab) =====
    with st.expander("🔍 Filters", expanded=True):
        filter_cols = st.columns(3)
        
        with filter_cols[0]:
            min_date, max_date = analyzer.get_date_range()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        with filter_cols[1]:
            routes = analyzer.get_unique_routes()
            selected_routes = st.multiselect("Routes", routes, default=[])
        
        with filter_cols[2]:
            min_trips = st.slider("Min Trips per Route", 1, 20, 5)
    
    # Apply filters
    if len(date_range) == 2:
        filtered_df = analyzer.apply_filters(
            start_date=date_range[0],
            end_date=date_range[1],
            routes=selected_routes if selected_routes else None
        )
    else:
        filtered_df = analyzer.df
    
    # ===== KPI ROW =====
    kpis = analyzer.get_kpis(filtered_df)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", format_compact_number(kpis.get('total_revenue', 0)))
    col2.metric("Total Profit", format_compact_number(kpis.get('total_profit', 0)))
    col3.metric("Profit Margin", format_pct(kpis.get('profit_margin', 0)))
    col4.metric("Cost/Mile", f"${kpis.get('cost_per_mile', 0):.3f}")
    col5.metric("Total Trips", f"{kpis.get('total_trips', 0):,}")
    
    st.markdown("---")
    
    # ===== TABS =====
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Trends", "🛣️ Route Analysis", "📉 Risk Analysis"])
    
    with tab1:
        st.subheader("Monthly Revenue vs Profit")
        fig = analyzer.plot_monthly_trends(filtered_df)
        if fig:
            st.pyplot(fig)
        
        # Monthly data table with export
        st.subheader("📋 Monthly Data")
        monthly_df = analyzer.get_monthly_df(filtered_df)
        st.dataframe(monthly_df, use_container_width=True)
        
        export_cols = st.columns(2)
        with export_cols[0]:
            export_to_csv(monthly_df, "financial_monthly")
        with export_cols[1]:
            export_to_excel(monthly_df, "financial_monthly")
    
    with tab2:
        col_top, col_bottom = st.columns(2)
        
        with col_top:
            st.subheader("🏆 Top Profitable Routes")
            fig = analyzer.plot_route_profitability(filtered_df)
            if fig:
                st.pyplot(fig)
        
        with col_bottom:
            st.subheader("⚠️ Underperforming Routes")
            fig = analyzer.plot_worst_routes(filtered_df)
            if fig:
                st.pyplot(fig)
        
        # Route data table with export
        st.subheader("📋 All Routes Data")
        route_df = analyzer.get_route_stats_df(filtered_df, min_trips=min_trips)
        st.dataframe(route_df, use_container_width=True)
        
        export_cols = st.columns(2)
        with export_cols[0]:
            export_to_csv(route_df, "route_analysis")
        with export_cols[1]:
            export_to_excel(route_df, "route_analysis")
    
    with tab3:
        st.subheader("Profitability Distribution (Risk Analysis)")
        fig = analyzer.plot_profit_distribution(filtered_df)
        if fig:
            st.pyplot(fig)
        
        st.subheader("Cost Per Mile Trend")
        fig = analyzer.plot_cost_trend(filtered_df)
        if fig:
            st.pyplot(fig)
        
        # Alerts
        st.subheader("⚠️ Financial Alerts")
        alerts = analyzer.get_alerts(filtered_df)
        if alerts:
            for alert in alerts:
                display_alert(alert)
        else:
            st.success("✅ No financial concerns detected!")


def render_operational_page(data):
    """Render the Operational Efficiency page"""
    st.title("⏱️ Operational Efficiency Dashboard")
    
    analyzer = OperationalAnalyzer(data)
    
    # ===== FILTERS =====
    with st.expander("🔍 Filters", expanded=True):
        filter_cols = st.columns(4)
        
        with filter_cols[0]:
            min_date, max_date = analyzer.get_date_range()
            if min_date and max_date:
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                date_range = None
        
        with filter_cols[1]:
            routes = analyzer.get_unique_values('route_name')
            selected_routes = st.multiselect("Routes", routes[:50], default=[])
        
        with filter_cols[2]:
            trucks = analyzer.get_unique_values('truck_id')
            selected_trucks = st.multiselect("Trucks", trucks[:30], default=[])
        
        with filter_cols[3]:
            on_time_filter = st.selectbox("Status", ["All", "On-Time Only", "Delayed Only"])
    
    # Apply filters
    status_map = {"All": None, "On-Time Only": "on_time", "Delayed Only": "delayed"}
    if date_range and len(date_range) == 2:
        filtered_df = analyzer.filter_data(
            start_date=date_range[0],
            end_date=date_range[1],
            routes=selected_routes if selected_routes else None,
            trucks=selected_trucks if selected_trucks else None,
            on_time_status=status_map.get(on_time_filter)
        )
    else:
        filtered_df = analyzer.op_data
    
    # ===== KPI ROW =====
    kpis = analyzer.get_kpis(filtered_df)
    delay_stats = analyzer.get_delay_stats(filtered_df)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("On-Time Rate", format_pct(kpis.get('on_time_rate', 0)))
    col2.metric("Fleet Utilization", format_pct(kpis.get('fleet_utilization', 0)))
    col3.metric("Avg Delay", f"{delay_stats.get('avg_delay', 0):.0f} min")
    col4.metric("Total Trips", f"{kpis.get('total_trips', 0):,}")
    
    st.markdown("---")
    
    # ===== TABS =====
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🛣️ Routes", "🚛 Trucks", "👨‍✈️ Drivers"])
    
    with tab1:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("On-Time vs Delayed")
            fig = analyzer.plot_ontime_distribution(filtered_df)
            if fig:
                st.pyplot(fig)
        
        with chart_col2:
            st.subheader("Monthly On-Time Trend")
            fig = analyzer.plot_ontime_trend(filtered_df)
            if fig:
                st.pyplot(fig)
        
        st.subheader("📊 Delay Distribution")
        fig = analyzer.plot_delay_distribution(filtered_df)
        if fig:
            st.pyplot(fig)
    
    with tab2:
        st.subheader("Route On-Time Performance")
        fig = analyzer.plot_route_performance(filtered_df)
        if fig:
            st.pyplot(fig)
        
        st.subheader("📋 Route Data")
        route_df = analyzer.get_route_ontime_df(filtered_df)
        st.dataframe(route_df, use_container_width=True)
        
        export_cols = st.columns(2)
        with export_cols[0]:
            export_to_csv(route_df, "route_performance")
    
    with tab3:
        st.subheader("Truck Reliability Ranking")
        fig = analyzer.plot_truck_reliability(filtered_df)
        if fig:
            st.pyplot(fig)
        
        st.subheader("📋 Truck Data")
        truck_df = analyzer.get_truck_reliability_df(filtered_df)
        st.dataframe(truck_df, use_container_width=True)
        
        export_to_csv(truck_df, "truck_reliability")
    
    with tab4:
        st.subheader("Driver Reliability Ranking")
        driver_df = analyzer.get_driver_reliability_df(filtered_df)
        st.dataframe(driver_df, use_container_width=True)
        
        export_to_csv(driver_df, "driver_reliability")
    
    # Alerts section
    st.markdown("---")
    st.subheader("⚠️ Operational Alerts")
    alerts = analyzer.get_alerts(filtered_df)
    if alerts:
        for alert in alerts:
            display_alert(alert)
    else:
        st.success("✅ All operational metrics within target!")


def render_driver_page(data):
    """Render the Driver Performance page"""
    st.title("👨‍✈️ Driver Performance Dashboard")
    
    analyzer = DriverPerformanceAnalyzer(data)
    
    # ===== FILTERS =====
    with st.expander("🔍 Filters & Search", expanded=True):
        filter_cols = st.columns(4)
        
        with filter_cols[0]:
            search_query = st.text_input("🔍 Search Driver", "")
        
        with filter_cols[1]:
            min_revenue = st.number_input("Min Revenue ($)", min_value=0, value=0, step=1000)
        
        with filter_cols[2]:
            min_otd = st.slider("Min On-Time Rate", 0.0, 1.0, 0.0, 0.01)
        
        with filter_cols[3]:
            sort_by = st.selectbox("Sort By", ["Score", "Revenue", "MPG", "On-Time Rate", "Idle Hours"])
    
    # ===== KPI ROW =====
    kpis = analyzer.get_kpis()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Revenue", format_compact_number(kpis.get('avg_revenue', 0)))
    col2.metric("Avg MPG", f"{kpis.get('avg_mpg', 0):.1f}")
    col3.metric("Avg On-Time", format_pct(kpis.get('avg_otd', 0)))
    col4.metric("Total Incidents", f"{kpis.get('total_incidents', 0)}")
    
    st.markdown("---")
    
    # Get leaderboard with filters
    if search_query:
        leaderboard = analyzer.search_driver(search_query)
        st.info(f"🔍 Showing search results for: '{search_query}'")
    else:
        leaderboard = analyzer.get_leaderboard_df(
            min_revenue=min_revenue,
            min_otd=min_otd,
            sort_by=sort_by
        )
    
    # ===== LEADERBOARD =====
    st.subheader("🏆 Driver Leaderboard")
    
    if not leaderboard.empty:
        # Format for display
        display_df = leaderboard.copy()
        st.dataframe(
            display_df[['Driver Name', 'Score', 'Revenue', 'MPG', 'On-Time Rate', 'Idle Hours', 'Incidents']].style.format({
                'Score': '{:.1f}',
                'Revenue': '${:,.0f}',
                'MPG': '{:.1f}',
                'On-Time Rate': '{:.1%}',
                'Idle Hours': '{:.1f}'
            }),
            use_container_width=True
        )
        
        export_to_csv(display_df, "driver_leaderboard")
    else:
        st.warning("No drivers match the current filters.")
    
    st.markdown("---")
    
    # ===== CHARTS =====
    st.subheader("🎯 Performance Matrix")
    fig = analyzer.plot_performance_matrix()
    if fig:
        st.pyplot(fig)
    
    st.markdown("---")
    
    st.subheader("🔗 Safety Correlation")
    fig = analyzer.plot_safety_heatmap()
    if fig:
        st.pyplot(fig)
    
    # Driver comparison
    st.subheader("📊 Top Drivers Comparison")
    fig = analyzer.plot_driver_comparison()
    if fig:
        st.pyplot(fig)
    
    # Alerts
    st.markdown("---")
    st.subheader("⚠️ Driver Alerts")
    alerts = analyzer.get_alerts()
    if alerts:
        for alert in alerts:
            display_alert(alert)
    else:
        st.success("✅ All driver metrics are healthy!")


def render_fleet_costs_page(data):
    """Render the Fleet Costs (Fuel & Maintenance) page"""
    st.title("⛽ Fleet Costs Dashboard")
    
    analyzer = FuelMaintenanceAnalyzer(data)
    
    # ===== FILTERS =====
    with st.expander("🔍 Filters", expanded=True):
        filter_cols = st.columns(3)
        
        with filter_cols[0]:
            trucks = analyzer.get_unique_trucks()
            selected_trucks = st.multiselect("Select Trucks", trucks[:30], default=[])
        
        with filter_cols[1]:
            top_n = st.slider("Show Top N Trucks", 3, 15, 5)
        
        with filter_cols[2]:
            cost_view = st.selectbox("View", ["All Costs", "Fuel Only", "Maintenance Only"])
    
    truck_filter = selected_trucks if selected_trucks else None
    
    # ===== KPI ROW =====
    kpis = analyzer.get_kpis(truck_filter)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Fuel Cost", format_compact_number(kpis.get('total_fuel_cost', 0)))
    col2.metric("Total Maintenance", format_compact_number(kpis.get('total_maint_cost', 0)))
    col3.metric("Fleet MPG", f"{kpis.get('fleet_mpg', 0):.1f}")
    col4.metric("Avg Downtime", f"{kpis.get('avg_downtime', 0):.1f} hrs")
    
    st.markdown("---")
    
    # ===== TABS =====
    tab1, tab2, tab3 = st.tabs(["💰 Cost Overview", "🔧 Maintenance Risk", "📈 Trends"])
    
    with tab1:
        st.subheader(f"Top {top_n} Highest Cost Trucks")
        fig = analyzer.plot_cost_distribution(truck_filter, top_n=top_n)
        if fig:
            st.pyplot(fig)
        
        st.subheader("📋 Cost Details by Truck")
        cost_df = analyzer.get_cost_by_truck_df(truck_filter)
        st.dataframe(cost_df, use_container_width=True)
        
        export_to_csv(cost_df, "fleet_costs")
    
    with tab2:
        st.subheader("⚠️ Maintenance Risk Analysis")
        st.markdown("Trucks in the upper-right quadrant require immediate attention (high mileage + old age)")
        
        fig = analyzer.plot_maintenance_risk(truck_filter)
        if fig:
            st.pyplot(fig)
        
        st.subheader("🚨 High-Risk Trucks")
        risky = analyzer.get_high_risk_trucks()
        if not risky.empty:
            st.dataframe(risky.style.apply(
                lambda x: ['background-color: #fee2e2' if v == 'High' else 
                          'background-color: #fef3c7' if v == 'Medium' else '' 
                          for v in x], 
                subset=['Risk Level']
            ), use_container_width=True)
        else:
            st.success("✅ No high-risk trucks detected!")
    
    with tab3:
        st.subheader("Fuel Cost & Price Trend")
        fig = analyzer.plot_fuel_trend(truck_filter)
        if fig:
            st.pyplot(fig)
        
        st.subheader("Maintenance Types Breakdown")
        fig = analyzer.plot_maintenance_types(truck_filter)
        if fig:
            st.pyplot(fig)
    
    # Alerts
    st.markdown("---")
    st.subheader("⚠️ Fleet Cost Alerts")
    alerts = analyzer.get_alerts(truck_filter)
    if alerts:
        for alert in alerts:
            display_alert(alert)
    else:
        st.success("✅ Fleet costs within normal parameters!")


def render_predictive_page(data):
    """Render the Predictive Insights page"""
    st.title("📈 Predictive Insights & Analytics")
    st.info("Advanced analytics based on historical patterns and trend analysis")
    
    vis = AdvancedVisualizer(data)
    
    # ===== TABS =====
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Growth Analysis", "💰 Profitability", "🔗 Safety Insights", "📅 Seasonality"])
    
    with tab1:
        st.subheader("Historical Load Volume Growth")
        
        loads = data.get('loads')
        if loads is not None:
            loads_copy = loads.copy()
            loads_copy['load_date'] = pd.to_datetime(loads_copy['load_date'], errors='coerce')
            loads_copy['month'] = loads_copy['load_date'].dt.to_period('M')
            monthly_loads = loads_copy.groupby('month').size()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Monthly Load Volume")
                st.bar_chart(monthly_loads)
            
            with col2:
                st.subheader("Growth Rate (%)")
                growth = monthly_loads.pct_change().fillna(0) * 100
                st.line_chart(growth)
    
    with tab2:
        st.subheader("Profitability Risk Distribution")
        fig = vis.profit_distribution()
        if fig:
            st.pyplot(fig)
        
        st.markdown("""
        ### 💡 Key Insights
        - Trips in the **red zone** (left of zero) are loss-making
        - Focus on routes and customers with consistently negative margins
        - Review fuel surcharges and accessorial charges for unprofitable trips
        """)
    
    with tab3:
        st.subheader("Safety vs. Efficiency Correlation")
        fig = vis.safety_efficiency_heatmap()
        if fig:
            st.pyplot(fig)
        
        st.markdown("""
        ### 💡 Interpretation Guide
        - **Positive correlation** (red): Higher values move together
        - **Negative correlation** (blue): One increases as other decreases
        - Watch for safety incidents correlating with high idle time or low MPG
        """)
    
    with tab4:
        st.subheader("Seasonal Load Patterns")
        fig = vis.seasonality_heatmap()
        if fig:
            st.pyplot(fig)
        
        st.markdown("""
        ### 💡 How to Use This
        - Identify peak days and months for staffing optimization
        - Plan maintenance during low-volume periods
        - Adjust pricing strategies for high-demand periods
        """)


def render_alerts_page(data, alerts_engine):
    """Render the Alerts Center page"""
    st.title("⚠️ Fleet Alerts Center")
    
    # Get all alerts
    all_alerts = alerts_engine.get_all_alerts()
    counts = alerts_engine.get_alert_count()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Critical", counts['critical'])
    col2.metric("🟡 Warning", counts['warning'])
    col3.metric("🟢 Info", counts['info'])
    col4.metric("📊 Total", counts['total'])
    
    st.markdown("---")
    
    # Filter by type
    alert_filter = st.selectbox("Filter by Severity", ["All", "Critical Only", "Warnings Only", "Info Only"])
    
    if alert_filter == "Critical Only":
        filtered_alerts = [a for a in all_alerts if a.get('type') == 'critical']
    elif alert_filter == "Warnings Only":
        filtered_alerts = [a for a in all_alerts if a.get('type') == 'warning']
    elif alert_filter == "Info Only":
        filtered_alerts = [a for a in all_alerts if a.get('type') == 'info']
    else:
        filtered_alerts = all_alerts
    
    # Display alerts
    if filtered_alerts:
        for alert in filtered_alerts:
            source_icons = {'Financial': '💰', 'Operations': '⏱️', 'Drivers': '👨‍✈️', 'Fleet': '⛽'}
            source = alert.get('source', 'Unknown')
            
            with st.container():
                col_icon, col_content = st.columns([1, 10])
                with col_icon:
                    st.markdown(f"### {source_icons.get(source, '📊')}")
                with col_content:
                    display_alert(alert)
                    st.caption(f"Source: {source}")
            st.markdown("---")
    else:
        st.success("✅ No alerts matching the current filter!")
    
    # Export alerts
    if all_alerts:
        st.subheader("📥 Export Alerts")
        alerts_df = pd.DataFrame(all_alerts)
        export_to_csv(alerts_df, "fleet_alerts")


def render_settings_page():
    """Render the Settings page"""
    st.title("⚙️ Settings")
    
    # Theme toggle

    
    st.markdown("---")
    
    # Alert thresholds
    st.subheader("⚠️ Alert Thresholds")
    st.info("Customize when alerts are triggered")
    
    configs = AlertThresholdConfig.get_all_configs()
    
    cols = st.columns(2)
    for i, (key, config) in enumerate(configs.items()):
        with cols[i % 2]:
            st.number_input(
                f"{config['label']} ({config['unit']})",
                value=config['value'],
                key=f"threshold_{key}"
            )
    
    if st.button("💾 Save Threshold Settings"):
        st.success("✅ Settings saved! (Note: Full implementation would persist these)")


def render_info_page():
    """Render the Info page"""
    st.title("ℹ️ Info")
    
    st.markdown("""
    **Fleet Analytics Platform** v1.0.0
    
    A comprehensive logistics optimization and fleet management solution designed for enterprise-scale operations.
    
    ### Core Modules
    - **Financial Intelligence**: Advanced revenue tracking and profit margin analysis.
    - **Operational Efficiency**: Real-time delivery performance and route optimization.
    - **Driver Performance**: Scorecarding and safety incident correlation.
    - **Fleet Costs**: Granular fuel and maintenance cost tracking.
    - **Predictive Analytics**: AI-driven trend forecasting and risk assessment.
    
    ### Support & Contact
    For technical support or feature requests, please contact the dedicated IT team:
    - **Email**: support@fleetsmart-analytics.com
    
    &copy; 2026 FleetSmart Analytics. All rights reserved.
    """)


# ============== RUN APPLICATION ==============
if __name__ == "__main__":
    main()