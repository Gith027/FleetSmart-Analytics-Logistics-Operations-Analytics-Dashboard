# driver_performance.py
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class DriverPerformanceAnalyzer:
    def __init__(self, processed_data):
        self.data = processed_data
        print("Driver Performance Analyzer ready!")

    def show_dashboard(self):
        print("\n" + "="*80)
        print("                DRIVER PERFORMANCE DASHBOARD")
        print("="*80)

        # Get required tables
        drivers = self.data.get('drivers')
        driver_monthly = self.data.get('driver_monthly_metrics')
        incidents = self.data.get('safety_incidents')

        # Check if we have the main data
        if driver_monthly is None or drivers is None or driver_monthly.empty:
            print("Not enough data: Missing driver_monthly_metrics or drivers table.")
            return

        # Make a working copy
        df = driver_monthly.copy()

        # Fix numeric columns that might have been turned into dates
        numeric_columns = ['total_revenue', 'average_mpg', 'average_idle_hours', 'on_time_delivery_rate']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert anything wrong to NaN

        # Fill missing numbers with safe defaults
        df['total_revenue'].fillna(0, inplace=True)
        df['average_mpg'].fillna(0, inplace=True)
        df['average_idle_hours'].fillna(0, inplace=True)
        df['on_time_delivery_rate'].fillna(0, inplace=True)

        # Add driver names
        df = df.merge(drivers[['driver_id', 'first_name', 'last_name']], on='driver_id', how='left')
        df['full_name'] = (df['first_name'].fillna('') + " " + df['last_name'].fillna('')).str.strip()
        df['full_name'] = df['full_name'].replace('', 'Unknown Driver')

        # Add safety incidents
        if incidents is not None and not incidents.empty:
            incident_counts = incidents.groupby('driver_id').size().reset_index(name='incident_count')
            df = df.merge(incident_counts, on='driver_id', how='left')
            df['incident_count'].fillna(0, inplace=True)
        else:
            df['incident_count'] = 0

        # === Key Metrics ===
        avg_revenue = df['total_revenue'].mean()
        avg_mpg = df['average_mpg'].mean()
        avg_idle = df['average_idle_hours'].mean()
        avg_otd = df['on_time_delivery_rate'].mean() * 100

        print(" KEY DRIVER METRICS (Fleet Average)")
        print("-" * 50)
        print(f" Average Monthly Revenue : ${avg_revenue:,.0f}")
        print(f" Average MPG             : {avg_mpg:.1f}")
        print(f" Average Idle Hours      : {avg_idle:.1f} hrs/trip")
        print(f" On-Time Delivery Rate   : {avg_otd:.1f}%")
        print(f" Total Safety Incidents  : {int(df['incident_count'].sum())}")
        print()

        # === Performance Score & Top 5 Drivers ===
        print(" TOP 5 BEST PERFORMING DRIVERS")
        print("-" * 70)

        # Create a smart score
        df['score'] = 0
        df['score'] += df['total_revenue'] / 1000 * 0.5          # Revenue matters a lot
        df['score'] += df['average_mpg'] * 4                    # Good fuel efficiency
        df['score'] += df['on_time_delivery_rate'] * 40         # On-time is very important
        df['score'] -= df['average_idle_hours'] * 3             # Less idle = better
        df['score'] -= df['incident_count'] * 15                 # No incidents = better

        # Get top 5
        top5 = df.nlargest(5, 'score')

        if len(top5) == 0:
            print(" No performance data available to rank drivers.")
        else:
            for i, row in top5.iterrows():
                name = row['full_name'][:25].ljust(25)
                revenue = int(row['total_revenue'])
                mpg = row['average_mpg']
                otd = row['on_time_delivery_rate'] * 100
                incidents = int(row['incident_count'])
                print(f" {i+1}. {name} → Revenue: ${revenue:>8,} | MPG: {mpg:>4.1f} | OTD: {otd:>5.1f}% | Incidents: {incidents}")

        # === Alerts ===
        print("\n" + "="*80)
        if avg_otd < 85:
            print("ALERT: On-Time Delivery below 85% – Action needed!")
        if avg_idle > 5:
            print("ALERT: High idle time – Drivers may need training!")
        if df['incident_count'].sum() > 8:
            print(f"ALERT: {int(df['incident_count'].sum())} safety incidents – Review safety protocols!")
        if avg_mpg < 6.0:
            print("ALERT: Low fleet MPG – Check routes, trucks, or driving habits!")

        print("\nDRIVER PERFORMANCE ANALYSIS COMPLETE!")
        print("="*80)