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

    # ============== NEW STREAMLIT HELPER METHODS ==============
    
    def get_kpis(self, truck_ids=None):
        """Returns dictionary of fuel and maintenance KPIs"""
        fuel = self.data.get('fuel_purchases')
        maint = self.data.get('maintenance_records')
        truck_monthly = self.data.get('truck_utilization_metrics')
        
        if fuel is None or maint is None:
            return {}
        
        # Apply truck filter if provided
        if truck_ids and len(truck_ids) > 0:
            fuel = fuel[fuel['truck_id'].isin(truck_ids)]
            maint = maint[maint['truck_id'].isin(truck_ids)]
        
        avg_mpg = 0
        if truck_monthly is not None and 'average_mpg' in truck_monthly.columns:
            if truck_ids and len(truck_ids) > 0:
                filtered_monthly = truck_monthly[truck_monthly['truck_id'].isin(truck_ids)]
                avg_mpg = filtered_monthly['average_mpg'].mean() if not filtered_monthly.empty else 0
            else:
                avg_mpg = truck_monthly['average_mpg'].mean()
        
        return {
            'total_fuel_cost': fuel['total_cost'].sum(),
            'total_gallons': fuel['gallons'].sum(),
            'avg_price_gallon': fuel['price_per_gallon'].mean(),
            'fleet_mpg': avg_mpg,
            'total_maint_cost': maint['total_cost'].sum(),
            'maint_events': len(maint),
            'avg_downtime': maint['downtime_hours'].mean() if 'downtime_hours' in maint.columns else 0,
            'total_cost': fuel['total_cost'].sum() + maint['total_cost'].sum()
        }
    
    def get_cost_by_truck_df(self, truck_ids=None):
        """Returns fuel + maintenance cost per truck as DataFrame"""
        fuel = self.data.get('fuel_purchases')
        maint = self.data.get('maintenance_records')
        trucks = self.data.get('trucks')
        
        if fuel is None or maint is None:
            return pd.DataFrame()
        
        # Apply filter if provided
        if truck_ids and len(truck_ids) > 0:
            fuel = fuel[fuel['truck_id'].isin(truck_ids)]
            maint = maint[maint['truck_id'].isin(truck_ids)]
        
        fuel_cost = fuel.groupby('truck_id')['total_cost'].sum().rename('Fuel Cost')
        maint_cost = maint.groupby('truck_id')['total_cost'].sum().rename('Maintenance Cost')
        
        # Count maintenance events
        maint_count = maint.groupby('truck_id').size().rename('Maint Events')
        
        # Combine
        cost_df = pd.concat([fuel_cost, maint_cost, maint_count], axis=1).fillna(0)
        cost_df['Total Cost'] = cost_df['Fuel Cost'] + cost_df['Maintenance Cost']
        cost_df = cost_df.reset_index()
        cost_df.columns = ['Truck ID', 'Fuel Cost', 'Maintenance Cost', 'Maint Events', 'Total Cost']
        
        # Add truck info if available
        if trucks is not None:
            truck_info = trucks[['truck_id']].copy()
            if 'unit_number' in trucks.columns:
                truck_info['Unit'] = trucks['unit_number']
            if 'model_year' in trucks.columns:
                truck_info['Year'] = trucks['model_year']
            cost_df = cost_df.merge(truck_info, left_on='Truck ID', right_on='truck_id', how='left')
            cost_df = cost_df.drop(columns=['truck_id'], errors='ignore')
        
        return cost_df.sort_values('Total Cost', ascending=False)
    
    def get_maintenance_types_df(self, truck_ids=None):
        """Returns maintenance breakdown by type"""
        maint = self.data.get('maintenance_records')
        if maint is None:
            return pd.DataFrame()
        
        # Apply filter
        if truck_ids and len(truck_ids) > 0:
            maint = maint[maint['truck_id'].isin(truck_ids)]
        
        # Check for maintenance type column
        type_col = next((col for col in maint.columns if 'type' in col.lower() or 'category' in col.lower()), None)
        
        if type_col:
            type_stats = maint.groupby(type_col).agg({
                'total_cost': ['sum', 'count', 'mean'],
                'downtime_hours': 'sum' if 'downtime_hours' in maint.columns else 'count'
            }).reset_index()
            type_stats.columns = ['Maintenance Type', 'Total Cost', 'Event Count', 'Avg Cost', 'Total Downtime']
        else:
            # If no type column, create summary by truck
            type_stats = maint.groupby('truck_id').agg({
                'total_cost': ['sum', 'count']
            }).reset_index()
            type_stats.columns = ['Truck ID', 'Total Cost', 'Event Count']
        
        return type_stats.sort_values('Total Cost', ascending=False)
    
    def get_fuel_trend_df(self, truck_ids=None):
        """Returns fuel cost trend over time"""
        fuel = self.data.get('fuel_purchases')
        if fuel is None:
            return pd.DataFrame()
        
        # Apply filter
        if truck_ids and len(truck_ids) > 0:
            fuel = fuel[fuel['truck_id'].isin(truck_ids)]
        
        # Convert date
        date_col = next((col for col in fuel.columns if 'date' in col.lower()), None)
        if not date_col:
            return pd.DataFrame()
        
        fuel_copy = fuel.copy()
        fuel_copy[date_col] = pd.to_datetime(fuel_copy[date_col], errors='coerce')
        fuel_copy['Month'] = fuel_copy[date_col].dt.to_period('M').astype(str)
        
        trend = fuel_copy.groupby('Month').agg({
            'total_cost': 'sum',
            'gallons': 'sum',
            'price_per_gallon': 'mean'
        }).reset_index()
        trend.columns = ['Month', 'Total Cost', 'Gallons', 'Avg Price/Gallon']
        
        return trend
    
    def get_unique_trucks(self):
        """Returns list of truck IDs for filter dropdown"""
        trucks = self.data.get('trucks')
        if trucks is None:
            return []
        return sorted(trucks['truck_id'].dropna().unique().tolist())
    
    def filter_by_truck(self, truck_ids):
        """Returns filtered data dictionaries for trucks"""
        if not truck_ids or len(truck_ids) == 0:
            return self.data
        
        filtered = {}
        for key, df in self.data.items():
            if df is not None and 'truck_id' in df.columns:
                filtered[key] = df[df['truck_id'].isin(truck_ids)]
            else:
                filtered[key] = df
        return filtered
    
    def get_high_risk_trucks(self, mileage_threshold=500000, age_threshold=10):
        """Returns trucks that exceed risk thresholds"""
        trucks = self.data.get('trucks')
        if trucks is None:
            return pd.DataFrame()
        
        df = trucks.copy()
        current_year = pd.Timestamp.now().year
        df['Age'] = current_year - df['model_year']
        
        # Find odometer column
        odo_col = next((col for col in df.columns if 'odometer' in col.lower()), None)
        if not odo_col:
            return pd.DataFrame()
        
        df['Mileage'] = df[odo_col]
        
        # Flag high risk
        df['High Mileage'] = df['Mileage'] > mileage_threshold
        df['High Age'] = df['Age'] > age_threshold
        df['Risk Level'] = 'Low'
        df.loc[df['High Mileage'] | df['High Age'], 'Risk Level'] = 'Medium'
        df.loc[df['High Mileage'] & df['High Age'], 'Risk Level'] = 'High'
        
        # Filter to only risky trucks
        risky = df[df['Risk Level'] != 'Low'][['truck_id', 'Mileage', 'Age', 'model_year', 'Risk Level']]
        risky.columns = ['Truck ID', 'Mileage', 'Age (Years)', 'Model Year', 'Risk Level']
        
        return risky.sort_values('Risk Level', ascending=False)
    
    def get_alerts(self, truck_ids=None):
        """Returns list of fuel/maintenance alerts"""
        kpis = self.get_kpis(truck_ids)
        alerts = []
        
        if kpis.get('fleet_mpg', 10) < 6.0:
            alerts.append({
                'type': 'warning',
                'title': 'Low Fleet Fuel Efficiency',
                'message': f"Average MPG: {kpis['fleet_mpg']:.1f}",
                'metric': 'Check idling and routes'
            })
        
        if kpis.get('avg_downtime', 0) > 8:
            alerts.append({
                'type': 'critical',
                'title': 'High Maintenance Downtime',
                'message': f"Average {kpis['avg_downtime']:.1f} hours per event",
                'metric': 'Impacting fleet utilization'
            })
        
        if kpis.get('total_maint_cost', 0) > 50000:
            alerts.append({
                'type': 'warning',
                'title': 'High Maintenance Spending',
                'message': f"Total: ${kpis['total_maint_cost']:,.0f}",
                'metric': 'Review preventive maintenance'
            })
        
        # Check for high-risk trucks
        risky_trucks = self.get_high_risk_trucks()
        if not risky_trucks.empty and 'Risk Level' in risky_trucks.columns:
            high_risk = risky_trucks[risky_trucks['Risk Level'] == 'High']
            if len(high_risk) > 0:
                alerts.append({
                    'type': 'critical',
                    'title': f'{len(high_risk)} High-Risk Trucks Detected',
                    'message': f"Trucks with high mileage AND age",
                    'metric': 'Schedule inspections'
                })
        
        return alerts

    def plot_cost_distribution(self, truck_ids=None, top_n=5):
        """Generates Stacked Bar Chart for Top N Costly Trucks"""
        import matplotlib.pyplot as plt
        
        cost_df = self.get_cost_by_truck_df(truck_ids)
        if cost_df.empty:
            return None
        
        top_trucks = cost_df.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = range(len(top_trucks))
        
        ax.bar(x, top_trucks['Fuel Cost'], label='Fuel', color='#e67e22')
        ax.bar(x, top_trucks['Maintenance Cost'], bottom=top_trucks['Fuel Cost'], 
               label='Maintenance', color='#e74c3c')
        
        ax.set_xticks(x)
        ax.set_xticklabels(top_trucks['Truck ID'].astype(str), rotation=0)
        ax.set_title(f"Top {top_n} Highest Cost Trucks")
        ax.set_ylabel("Total Cost ($)")
        ax.set_xlabel("Truck ID")
        ax.legend()
        
        # Add total labels
        for i, (_, row) in enumerate(top_trucks.iterrows()):
            ax.text(i, row['Total Cost'] + 500, f"${row['Total Cost']:,.0f}", 
                    ha='center', fontsize=9)
        
        plt.tight_layout()
        return fig

    def plot_maintenance_risk(self, truck_ids=None):
        """Generates Maintenance Risk Scatter (Mileage vs Age)"""
        import matplotlib.pyplot as plt
        
        trucks = self.data.get('trucks')
        if trucks is None:
            return None
        
        df = trucks.copy()
        if truck_ids and len(truck_ids) > 0:
            df = df[df['truck_id'].isin(truck_ids)]
        
        current_year = pd.Timestamp.now().year
        df['age'] = current_year - df['model_year']
        
        # Safe Odometer Column Retrieval
        odo_col = next((col for col in df.columns if 'odometer' in col.lower()), None)
        if not odo_col:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Color by risk level
        df['risk_score'] = (df[odo_col] / 100000) + (df['age'] * 2)
        scatter = ax.scatter(df[odo_col], df['age'], c=df['risk_score'], 
                            cmap='RdYlGn_r', s=200, alpha=0.8, edgecolors='white')
        
        # Add threshold lines
        ax.axvline(x=500000, color='#e74c3c', linestyle='--', alpha=0.7, label='High Mileage (500k)')
        ax.axhline(y=10, color='#f39c12', linestyle='--', alpha=0.7, label='High Age (10 years)')
        
        # Add quadrant shading
        ax.axvspan(500000, df[odo_col].max() * 1.1, alpha=0.1, color='red')
        ax.axhspan(10, df['age'].max() * 1.1, alpha=0.1, color='orange')
        
        ax.set_title("⚠️ Fleet Maintenance Risk Analysis")
        ax.set_xlabel("Odometer Reading (Miles)")
        ax.set_ylabel("Truck Age (Years)")
        plt.colorbar(scatter, ax=ax, label='Risk Score')
        ax.legend(loc='upper left')
        plt.tight_layout()
        return fig
    
    def plot_fuel_trend(self, truck_ids=None):
        """Generates fuel cost trend over time"""
        import matplotlib.pyplot as plt
        
        trend_df = self.get_fuel_trend_df(truck_ids)
        if trend_df.empty:
            return None
        
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Bar chart for total cost
        ax1.bar(trend_df['Month'], trend_df['Total Cost'], color='#3498db', alpha=0.7, label='Fuel Cost')
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Total Fuel Cost ($)', color='#3498db')
        ax1.tick_params(axis='y', labelcolor='#3498db')
        plt.xticks(rotation=45)
        
        # Line chart for price per gallon
        ax2 = ax1.twinx()
        ax2.plot(trend_df['Month'], trend_df['Avg Price/Gallon'], color='#e74c3c', 
                 marker='o', linewidth=2, label='Avg $/Gallon')
        ax2.set_ylabel('Price per Gallon ($)', color='#e74c3c')
        ax2.tick_params(axis='y', labelcolor='#e74c3c')
        
        ax1.set_title("Fuel Cost & Price Trend")
        fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9))
        plt.tight_layout()
        return fig
    
    def plot_maintenance_types(self, truck_ids=None):
        """Pie chart of maintenance types"""
        import matplotlib.pyplot as plt
        
        type_df = self.get_maintenance_types_df(truck_ids)
        if type_df.empty or 'Maintenance Type' not in type_df.columns:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = plt.cm.Set3(range(len(type_df)))
        
        wedges, texts, autotexts = ax.pie(
            type_df['Total Cost'], 
            labels=type_df['Maintenance Type'],
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.02] * len(type_df)
        )
        ax.set_title("Maintenance Cost by Type")
        plt.tight_layout()
        return fig
