# driver_performance.py
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class DriverPerformanceAnalyzer:
    def __init__(self, processed_data):
        self.data = processed_data
        print("Driver Performance Analyzer ready!")

    def show_dashboard(self):
        print("\n" + "="*80)
        print(" DRIVER PERFORMANCE DASHBOARD")
        print("="*80)

        drivers = self.data.get('drivers')
        driver_monthly = self.data.get('driver_monthly_metrics')
        incidents = self.data.get('safety_incidents')
        trips = self.data.get('trips')

        if driver_monthly is None or drivers is None:
            print("Missing driver_monthly_metrics or drivers data!")
            return

        # Merge name
        df = driver_monthly.merge(drivers[['driver_id', 'first_name', 'last_name']], on='driver_id', how='left')
        df['full_name'] = df['first_name'] + " " + df['last_name']

        # Safety incidents per driver
        if incidents is not None:
            incidents_count = incidents.groupby('driver_id').size().rename('incident_count')
            df = df.merge(incidents_count, on='driver_id', how='left').fillna({'incident_count': 0})

        # === Key Metrics ===
        avg_revenue = df['total_revenue'].mean()
        avg_mpg = df['average_mpg'].mean()
        avg_idle = df['average_idle_hours'].mean()
        avg_otd = df['on_time_delivery_rate'].mean() * 100

        print(f" Average Revenue per Driver : ${avg_revenue:,.0f}/month")
        print(f" Average MPG per Driver     : {avg_mpg:.1f}")
        print(f" Average Idle Hours         : {avg_idle:.1f} hrs/trip")
        print(f" On-Time Delivery Rate      : {avg_otd:.1f}%")
        print()

        # === Top 5 Best Drivers ===
        print("TOP 5 BEST PERFORMING DRIVERS")
        print("-" * 60)

        df['score'] = (
            df['total_revenue'] / 1000 * 0.4 +
            df['average_mpg'] * 5 +
            df['on_time_delivery_rate'] * 30 -
            df['average_idle_hours'] * 2 -
            df.get('incident_count', 0) * 10
        )

        top5 = df.nlargest(5, 'score')
        for i, row in top5.iterrows():
            name = row['full_name']
            revenue = row['total_revenue']
            mpg = row['average_mpg']
            incidents = int(row.get('incident_count', 0))
            print(f" {i+1}. {name:<25} → Revenue: ${revenue:,.0f} | MPG: {mpg:.1f} | Incidents: {incidents}")

        # === Alerts ===
        print("\n" + "="*80)
        if avg_otd < 85:
            print("ALERT: Low on-time delivery across drivers!")
        if avg_idle > 5:
            print("ALERT: High idle time — train drivers or check routes!")
        if df['incident_count'].sum() > 10:
            print("ALERT: Too many safety incidents!")
        print("DRIVER PERFORMANCE ANALYSIS COMPLETE!")
        print("="*80)