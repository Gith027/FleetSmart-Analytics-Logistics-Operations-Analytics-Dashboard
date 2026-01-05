# Visualization.py - Unified FleetSmart Visualization Module
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings


warnings.filterwarnings('ignore')

class PredictiveInsights:
    def __init__(self, processed_data):
        self.data = processed_data
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (20, 12)
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.titleweight'] = 'bold'

    def create_page(self, page_num, title):
        fig = plt.figure(figsize=(24, 14))
        fig.suptitle(f"FleetSmart Analytics - Page {page_num}: {title}", fontsize=24, fontweight='bold', y=0.98)
        gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4)
        return fig, gs

    def show_insights(self):
        # Legacy method for CLI multi-page dashboard
        # This can remain for compatibility or be refactored
        print("Use Streamlit methods for visualization")


class AdvancedVisualizer:
    def __init__(self, data):
        self.data = data
        sns.set_style("darkgrid")  # Better for advanced charts



    def profit_distribution(self):
        """Analyzes profit margins to find loss-making trips"""
        loads = self.data.get('loads')
        trips = self.data.get('trips')
        
        if loads is None or trips is None: return None
        
        # Merge to get Revenue vs Cost
        df = trips.merge(loads, on='load_id', how='left') # Changed to left just in case
        
        # Calculate Profit
        # We need to ensure we have profit data. If not, use proxy.
        if 'profit' not in df.columns:
            # Reconstruct profit if missing from loader
            # Revenue - (Fuel + Maint + Driver Pay + etc)
            # Simplified for visual: Revenue - Fuel - Accessorials
             # This assumes these columns exist
            fuel = df['fuel_surcharge'] if 'fuel_surcharge' in df.columns else 0
            acc = df['accessorial_charges'] if 'accessorial_charges' in df.columns else 0
            rev = df['revenue'] if 'revenue' in df.columns else 0
            df['profit_proxy'] = rev - fuel - acc
        else:
            df['profit_proxy'] = df['profit']

        df['profit_proxy'] = pd.to_numeric(df['profit_proxy'], errors='coerce').fillna(0)

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(df['profit_proxy'], kde=True, ax=ax, color='#2ecc71', bins=30)
        
        # Highlight Loss Area
        ymin, ymax = ax.get_ylim()
        try:
            min_val = df['profit_proxy'].min()
            if min_val < 0:
                ax.axvspan(min_val, 0, color='red', alpha=0.2, label='Loss-Making Zone')
        except:
            pass
        
        ax.set_title("Profitability Distribution (Risk Analysis)", fontsize=16)
        ax.set_xlabel("Profit per Trip ($)")
        ax.legend()
        return fig

    def safety_efficiency_heatmap(self):
        """Correlates Safety with Speed/Efficiency"""
        drivers = self.data.get('driver_monthly_metrics')
        incidents = self.data.get('safety_incidents')
        
        if drivers is None or incidents is None: return None
        
        # Aggregate incidents by driver
        safety_counts = incidents.groupby('driver_id').size().rename('accident_count')
        
        # Merge with performance metrics
        # Group driver metrics by driver_id (mean across months)
        driver_stats = drivers.groupby('driver_id').agg({
            'average_mpg': 'mean',
            'average_idle_hours': 'mean',
            'on_time_delivery_rate': 'mean'
        })
        
        df = driver_stats.join(safety_counts, how='left').fillna(0)
        
        # Correlation Matrix
        corr = df[['average_mpg', 'average_idle_hours', 'on_time_delivery_rate', 'accident_count']].corr()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=ax, vmin=-1, vmax=1)
        ax.set_title("Safety vs. Efficiency Correlation", fontsize=16)
        return fig

    def maintenance_risk_scatter(self):
        """Identifies vehicles at risk based on mileage and age"""
        trucks = self.data.get('trucks')
        if trucks is None: return None
        
        # Debug Schema
        print(f"DEBUG: Truck Columns: {trucks.columns.tolist()}")

        df = trucks.copy()
        # Calculate Age
        current_year = pd.Timestamp.now().year
        df['age'] = current_year - df['model_year']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Color by Year
        scatter = ax.scatter(df['odometer_reading'], df['age'], 
                             c=df['model_year'], cmap='plasma', s=200, alpha=0.8, edgecolors='w')
        
        # Add thresholds
        ax.axvline(x=500000, color='red', linestyle='--', alpha=0.5, label='High Mileage Alert (500k)')
        
        # Label trucks
        for i, row in df.iterrows():
            if row['odometer_reading'] > 400000 or row['age'] > 10:
                ax.text(row['odometer_reading'], row['age'], f" Truck {row['truck_id']}", fontsize=9)
        
        ax.set_title("⚠️ Fleet Maintenance Risk Analysis", fontsize=16)
        ax.set_xlabel("Odometer Reading (Miles)")
        ax.set_ylabel("Truck Age (Years)")
        plt.colorbar(scatter, ax=ax, label='Model Year')
        ax.legend()
        return fig

    def seasonality_heatmap(self):
        """Heatmap of Load Volume by Month vs. Day of Week"""
        loads = self.data.get('loads')
        if loads is None: return None
        
        df = loads.copy()
        df['load_date'] = pd.to_datetime(df['load_date'], errors='coerce')
        
        df['Month'] = df['load_date'].dt.month_name()
        df['Day'] = df['load_date'].dt.day_name()
        
        # Pivot
        pivot = df.pivot_table(index='Day', columns='Month', values='load_id', aggfunc='count', fill_value=0)
        
        # Sort indices
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December']
        
        # Filter existing months/days
        existing_days = [d for d in days_order if d in pivot.index]
        existing_months = [m for m in months_order if m in pivot.columns]
        
        pivot = pivot.reindex(index=existing_days, columns=existing_months)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(pivot, annot=True, fmt='d', cmap='Greens', ax=ax)
        ax.set_title("📅 Peak Seasonality: Volume Heatmap", fontsize=16)
        return fig