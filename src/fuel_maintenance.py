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

    def plot_cost_distribution(self):
        """Generates Stacked Bar Chart for Top 5 Costly Trucks"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        fuel = self.data.get('fuel_purchases')
        maint = self.data.get('maintenance_records')
        if fuel is None or maint is None: return None
        
        fuel_cost = fuel.groupby('truck_id')['total_cost'].sum()
        maint_cost = maint.groupby('truck_id')['total_cost'].sum()
        
        total_cost = pd.DataFrame({'Fuel': fuel_cost, 'Maintenance': maint_cost}).fillna(0)
        total_cost['Total'] = total_cost['Fuel'] + total_cost['Maintenance']
        
        top_trucks = total_cost.nlargest(5, 'Total')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        top_trucks[['Fuel', 'Maintenance']].plot(kind='bar', stacked=True, color=['#e67e22', '#e74c3c'], ax=ax)
        ax.set_title("Top 5 Highest Cost Trucks")
        ax.set_ylabel("Total Cost ($)")
        ax.set_xticklabels(top_trucks.index, rotation=0)
        return fig

    def plot_maintenance_risk(self):
        """Generates Maintenance Risk Scatter (Mileage vs Age)"""
        import matplotlib.pyplot as plt
        
        trucks = self.data.get('trucks')
        if trucks is None: return None
        
        df = trucks.copy()
        current_year = pd.Timestamp.now().year
        df['age'] = current_year - df['model_year']
        
        # Safe Odometer Column Retrieval
        odo_col = next((col for col in df.columns if 'odometer' in col.lower()), None)
        if not odo_col:
            print("Warning: No odometer column found in trucks data.")
            return None
            
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(df[odo_col], df['age'], c=df['model_year'], cmap='plasma', s=200, alpha=0.8, edgecolors='w')
        
        ax.axvline(x=500000, color='red', linestyle='--', alpha=0.5, label='High Mileage (500k)')
        
        ax.set_title("Fleet Maintenance Risk Analysis")
        ax.set_xlabel(f"Odometer Reading ({odo_col})")
        ax.set_ylabel("Truck Age (Years)")
        plt.colorbar(scatter, ax=ax, label='Model Year')
        ax.legend()
        return fig