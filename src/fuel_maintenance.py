# fuel_maintenance.py
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class FuelMaintenanceAnalyzer:
    def __init__(self, processed_data):
        self.data = processed_data
        print("Fuel & Maintenance Analyzer ready!")

    def show_dashboard(self):
        print("\n" + "="*80)
        print(" FUEL & MAINTENANCE PERFORMANCE DASHBOARD")
        print("="*80)

        # Load required tables
        fuel = self.data.get('fuel_purchases')
        maint = self.data.get('maintenance_records')
        trucks = self.data.get('trucks')
        truck_monthly = self.data.get('truck_utilization_metrics')

        if fuel is None or maint is None:
            print("Missing fuel_purchases or maintenance_records data!")
            return

        # === Fuel KPIs ===
        total_fuel_cost = fuel['total_cost'].sum()
        total_gallons = fuel['gallons'].sum()
        avg_price_per_gallon = fuel['price_per_gallon'].mean()
        avg_mpg_fleet = truck_monthly['average_mpg'].mean() if 'average_mpg' in truck_monthly.columns else 0

        print(f" Total Fuel Cost           : ${total_fuel_cost:,.0f}")
        print(f" Total Gallons Purchased   : {total_gallons:,.0f} gallons")
        print(f" Avg Price per Gallon      : ${avg_price_per_gallon:.2f}")
        print(f" Fleet Average MPG         : {avg_mpg_fleet:.1f} mpg")
        print()

        # === Maintenance KPIs ===
        total_maint_cost = maint['total_cost'].sum()
        avg_downtime_per_event = maint['downtime_hours'].mean()
        maint_events = len(maint)

        print(f" Total Maintenance Cost    : ${total_maint_cost:,.0f}")
        print(f" Total Maintenance Events  : {maint_events:,}")
        print(f" Avg Downtime per Event    : {avg_downtime_per_event:.1f} hours")
        print()

        # === Top 5 Most Expensive Trucks (Maintenance + Fuel) ===
        print("TOP 5 MOST EXPENSIVE TRUCKS (Fuel + Maintenance)")
        print("-" * 60)

        # Fuel cost per truck
        fuel_by_truck = fuel.groupby('truck_id')['total_cost'].sum().rename('fuel_cost')

        # Maintenance cost per truck
        maint_by_truck = maint.groupby('truck_id')['total_cost'].sum().rename('maint_cost')

        # Combine
        cost_by_truck = pd.concat([fuel_by_truck, maint_by_truck], axis=1).fillna(0)
        cost_by_truck['total_cost'] = cost_by_truck['fuel_cost'] + cost_by_truck['maint_cost']
        cost_by_truck = cost_by_truck.nlargest(5, 'total_cost')

        for truck_id, row in cost_by_truck.iterrows():
            unit = trucks[trucks['truck_id'] == truck_id]['unit_number'].iloc[0] if truck_id in trucks['truck_id'].values else "Unknown"
            print(f" Truck {unit} (ID: {truck_id}) → ${row['total_cost']:,.0f} (Fuel: ${row['fuel_cost']:,.0f}, Maint: ${row['maint_cost']:,.0f})")

        # === Alerts ===
        print("\n" + "="*80)
        if avg_mpg_fleet < 6.0:
            print("ALERT: Low fleet MPG! Check idling, routing, or truck health.")
        if avg_downtime_per_event > 8:
            print("ALERT: High downtime — impacting utilization!")
        if total_maint_cost > 50000:  # Example threshold
            print("ALERT: High maintenance spending this period.")
        print("FUEL & MAINTENANCE ANALYSIS COMPLETE!")
        print("="*80)