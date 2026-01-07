# driver_performance.py
import pandas as pd
import numpy as np
import difflib
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

    # ============== NEW STREAMLIT HELPER METHODS ==============
    
    def _prepare_driver_data(self):
        """Internal helper to prepare driver data with names and metrics"""
        drivers = self.data.get('drivers')
        driver_monthly = self.data.get('driver_monthly_metrics')
        incidents = self.data.get('safety_incidents')
        
        if driver_monthly is None or driver_monthly.empty:
            return pd.DataFrame()
        
        df = driver_monthly.copy()
        
        # Fix numeric columns
        numeric_columns = ['total_revenue', 'average_mpg', 'average_idle_hours', 'on_time_delivery_rate']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Add driver names
        if drivers is not None and not drivers.empty:
            name_cols = ['driver_id']
            if 'first_name' in drivers.columns:
                name_cols.append('first_name')
            if 'last_name' in drivers.columns:
                name_cols.append('last_name')
            df = df.merge(drivers[name_cols], on='driver_id', how='left')
            
            if 'first_name' in df.columns and 'last_name' in df.columns:
                df['Driver Name'] = (df['first_name'].fillna('') + ' ' + df['last_name'].fillna('')).str.strip()
            else:
                df['Driver Name'] = 'Driver ' + df['driver_id'].astype(str)
        else:
            df['Driver Name'] = 'Driver ' + df['driver_id'].astype(str)
        
        df['Driver Name'] = df['Driver Name'].replace('', 'Unknown Driver')
        
        # Add safety incidents
        if incidents is not None and not incidents.empty:
            incident_counts = incidents.groupby('driver_id').size().reset_index(name='Incidents')
            df = df.merge(incident_counts, on='driver_id', how='left')
            df['Incidents'] = df['Incidents'].fillna(0).astype(int)
        else:
            df['Incidents'] = 0
        
        return df
    
    def get_leaderboard_df(self, min_revenue=0, min_otd=0, sort_by='Score'):
        """Returns driver leaderboard as DataFrame for Streamlit display"""
        df = self._prepare_driver_data()
        if df.empty:
            return pd.DataFrame()
        
        # Aggregate by driver (in case of multiple months)
        leaderboard = df.groupby(['driver_id', 'Driver Name']).agg({
            'total_revenue': 'sum',
            'average_mpg': 'mean',
            'on_time_delivery_rate': 'mean',
            'average_idle_hours': 'mean',
            'Incidents': 'max'  # Take max incidents (they're counts per driver)
        }).reset_index()
        
        # Calculate score
        leaderboard['Score'] = (
            (leaderboard['total_revenue'] / 1000 * 0.5) +
            (leaderboard['average_mpg'] * 4) +
            (leaderboard['on_time_delivery_rate'] * 100 * 0.4) -
            (leaderboard['average_idle_hours'] * 3) -
            (leaderboard['Incidents'] * 15)
        ).round(1)
        
        # Rename columns for display
        leaderboard = leaderboard.rename(columns={
            'total_revenue': 'Revenue',
            'average_mpg': 'MPG',
            'on_time_delivery_rate': 'On-Time Rate',
            'average_idle_hours': 'Idle Hours'
        })
        
        # Apply filters
        if min_revenue > 0:
            leaderboard = leaderboard[leaderboard['Revenue'] >= min_revenue]
        if min_otd > 0:
            leaderboard = leaderboard[leaderboard['On-Time Rate'] >= min_otd]
        
        # Sort
        if sort_by in leaderboard.columns:
            ascending = sort_by in ['Idle Hours', 'Incidents']
            leaderboard = leaderboard.sort_values(sort_by, ascending=ascending)
        else:
            leaderboard = leaderboard.sort_values('Score', ascending=False)
        
        return leaderboard
    
    def get_driver_details(self, driver_id):
        """Returns detailed stats for a single driver"""
        df = self._prepare_driver_data()
        if df.empty:
            return None
        
        driver_data = df[df['driver_id'] == driver_id]
        if driver_data.empty:
            return None
        
        # Aggregate monthly data
        details = {
            'driver_id': driver_id,
            'name': driver_data['Driver Name'].iloc[0],
            'total_revenue': driver_data['total_revenue'].sum(),
            'avg_revenue': driver_data['total_revenue'].mean(),
            'avg_mpg': driver_data['average_mpg'].mean(),
            'avg_idle': driver_data['average_idle_hours'].mean(),
            'on_time_rate': driver_data['on_time_delivery_rate'].mean(),
            'incidents': driver_data['Incidents'].max(),
            'months_active': len(driver_data)
        }
        
        return details
    
    def search_driver(self, query):
        """Search drivers by name (case-insensitive)"""
        df = self._prepare_driver_data()
        if df.empty or not query:
            return pd.DataFrame()
        
        query = query.lower().strip()
        matches = df[df['Driver Name'].str.lower().str.contains(query, na=False)]
        
        if matches.empty:
            # Fuzzy search fallback
            all_names = df['Driver Name'].dropna().unique()
            # Case-insensitive mapping
            name_map = {name.lower(): name for name in all_names}
            
            # Find close matches to the lowercased query
            # cutoff=0.4 allows for loose matching (handling typos and partial similarities)
            close = difflib.get_close_matches(query, name_map.keys(), n=5, cutoff=0.4)
            
            if close:
                matched_original_names = [name_map[m] for m in close]
                matches = df[df['Driver Name'].isin(matched_original_names)]
            else:
                return pd.DataFrame()
        
        # Return unique drivers with aggregated stats
        result = matches.groupby(['driver_id', 'Driver Name']).agg({
            'total_revenue': 'sum',
            'average_mpg': 'mean',
            'on_time_delivery_rate': 'mean',
            'average_idle_hours': 'mean',
            'Incidents': 'max'
        }).reset_index()

        # Calculate score (same formula as leaderboard)
        result['Score'] = (
            (result['total_revenue'] / 1000 * 0.5) +
            (result['average_mpg'] * 4) +
            (result['on_time_delivery_rate'] * 100 * 0.4) -
            (result['average_idle_hours'] * 3) -
            (result['Incidents'] * 15)
        ).round(1)
        
        # Rename columns for display
        result = result.rename(columns={
            'total_revenue': 'Revenue',
            'average_mpg': 'MPG',
            'on_time_delivery_rate': 'On-Time Rate',
            'average_idle_hours': 'Idle Hours'
        })
        
        return result
    
    def get_unique_drivers(self):
        """Returns list of driver names for dropdown"""
        df = self._prepare_driver_data()
        if df.empty:
            return []
        return sorted(df['Driver Name'].dropna().unique().tolist())
    
    def get_kpis(self):
        """Returns dictionary of fleet-wide driver KPIs"""
        df = self._prepare_driver_data()
        if df.empty:
            return {}
        
        return {
            'avg_revenue': df['total_revenue'].mean(),
            'avg_mpg': df['average_mpg'].mean(),
            'avg_idle': df['average_idle_hours'].mean(),
            'avg_otd': df['on_time_delivery_rate'].mean() * 100,
            'total_incidents': int(df.groupby('driver_id')['Incidents'].max().sum()),
            'total_drivers': df['driver_id'].nunique()
        }
    
    def get_alerts(self):
        """Returns list of driver-related alerts"""
        kpis = self.get_kpis()
        alerts = []
        
        if kpis.get('avg_otd', 100) < 85:
            alerts.append({
                'type': 'critical',
                'title': 'Driver On-Time Rate Below Target',
                'message': f"Fleet average: {kpis['avg_otd']:.1f}%, Target: 85%+",
                'metric': 'Action needed!'
            })
        
        if kpis.get('avg_idle', 0) > 5:
            alerts.append({
                'type': 'warning',
                'title': 'High Fleet Idle Time',
                'message': f"Drivers averaging {kpis['avg_idle']:.1f} idle hours",
                'metric': 'Consider driver training'
            })
        
        if kpis.get('total_incidents', 0) > 8:
            alerts.append({
                'type': 'critical',
                'title': 'Safety Concern: High Incident Count',
                'message': f"{kpis['total_incidents']} safety incidents recorded",
                'metric': 'Review safety protocols'
            })
        
        if kpis.get('avg_mpg', 10) < 6.0:
            alerts.append({
                'type': 'warning',
                'title': 'Low Fleet Fuel Efficiency',
                'message': f"Average MPG: {kpis['avg_mpg']:.1f}",
                'metric': 'Check driving habits'
            })
        
        # Check for problematic drivers
        leaderboard = self.get_leaderboard_df()
        if not leaderboard.empty:
            low_performers = leaderboard[leaderboard['Score'] < 20]
            if len(low_performers) > 0:
                names = low_performers['Driver Name'].head(3).tolist()
                alerts.append({
                    'type': 'warning',
                    'title': f'{len(low_performers)} Drivers with Low Performance Scores',
                    'message': f"Including: {', '.join(names[:2])}",
                    'metric': 'Consider coaching'
                })
        
        return alerts

    def plot_performance_matrix(self, df=None):
        """Generates Efficiency vs Revenue Scatter with Quadrants"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        leaderboard = df if df is not None else self.get_leaderboard_df()
        if leaderboard.empty:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create scatter plot
        scatter = sns.scatterplot(
            data=leaderboard, 
            x='MPG', 
            y='Revenue',
            size='Score', 
            sizes=(50, 400), 
            hue='Score',
            palette='viridis', 
            ax=ax,
            alpha=0.7
        )
        
        # Add quadrant lines
        mpg_mean = leaderboard['MPG'].mean()
        rev_mean = leaderboard['Revenue'].mean()
        ax.axvline(mpg_mean, color='#e74c3c', linestyle='--', alpha=0.5, label=f'Avg MPG: {mpg_mean:.1f}')
        ax.axhline(rev_mean, color='#e74c3c', linestyle='--', alpha=0.5, label=f'Avg Revenue: ${rev_mean:,.0f}')
        
        # Add quadrant labels
        ax.text(leaderboard['MPG'].max() * 0.95, leaderboard['Revenue'].max() * 0.95, 
                '⭐ Stars', fontsize=10, ha='right', color='#2ecc71', weight='bold')
        ax.text(leaderboard['MPG'].min() * 1.05, leaderboard['Revenue'].max() * 0.95, 
                '💰 High Earners', fontsize=10, ha='left', color='#f39c12', weight='bold')
        ax.text(leaderboard['MPG'].max() * 0.95, leaderboard['Revenue'].min() * 1.1, 
                '🌱 Efficient', fontsize=10, ha='right', color='#3498db', weight='bold')
        ax.text(leaderboard['MPG'].min() * 1.05, leaderboard['Revenue'].min() * 1.1, 
                '⚠️ Needs Improvement', fontsize=10, ha='left', color='#e74c3c', weight='bold')
        
        ax.set_title("Driver Performance Matrix: Efficiency vs Revenue")
        ax.set_xlabel("Fuel Efficiency (MPG)")
        ax.set_ylabel("Total Revenue ($)")
        ax.legend(loc='upper left', fontsize=8)
        plt.tight_layout()
        return fig

    def plot_safety_heatmap(self):
        """Generates Safety vs Efficiency Heatmap"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        drivers = self.data.get('driver_monthly_metrics')
        incidents = self.data.get('safety_incidents')
        if drivers is None or incidents is None:
            return None
        
        safety_counts = incidents.groupby('driver_id').size().rename('Incidents')
        driver_stats = drivers.groupby('driver_id').agg({
            'average_mpg': 'mean',
            'average_idle_hours': 'mean',
            'on_time_delivery_rate': 'mean'
        })
        
        df = driver_stats.join(safety_counts, how='left').fillna(0)
        df = df.rename(columns={
            'average_mpg': 'MPG',
            'average_idle_hours': 'Idle Hours',
            'on_time_delivery_rate': 'On-Time Rate'
        })
        
        corr = df[['MPG', 'Idle Hours', 'On-Time Rate', 'Incidents']].corr()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap='RdYlGn_r', fmt=".2f", ax=ax, 
                    vmin=-1, vmax=1, center=0,
                    linewidths=0.5, square=True)
        ax.set_title("Safety vs. Efficiency Correlation Matrix")
        plt.tight_layout()
        return fig
    
    def plot_driver_comparison(self, driver_ids=None, top_n=10):
        """Bar chart comparing top drivers by score"""
        import matplotlib.pyplot as plt
        
        leaderboard = self.get_leaderboard_df()
        if leaderboard.empty:
            return None
        
        if driver_ids:
            display = leaderboard[leaderboard['driver_id'].isin(driver_ids)]
        else:
            display = leaderboard.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71' if s >= 40 else '#f39c12' if s >= 20 else '#e74c3c' 
                  for s in display['Score']]
        
        bars = ax.barh(display['Driver Name'], display['Score'], color=colors)
        ax.axvline(x=40, color='#2ecc71', linestyle='--', alpha=0.7, label='Excellent')
        ax.axvline(x=20, color='#f39c12', linestyle='--', alpha=0.7, label='Good')
        
        ax.set_xlabel("Performance Score")
        ax.set_title(f"Top {len(display)} Drivers by Performance Score")
        ax.legend()
        plt.tight_layout()
        return fig
    
    def plot_metrics_radar(self, driver_id):
        """Radar chart for individual driver metrics (placeholder)"""
        # Note: Radar charts in matplotlib are complex; this is a simplified version
        import matplotlib.pyplot as plt
        import numpy as np
        
        details = self.get_driver_details(driver_id)
        if not details:
            return None
        
        # Normalize metrics to 0-100 scale
        kpis = self.get_kpis()
        
        categories = ['Revenue', 'MPG', 'On-Time', 'Low Idle', 'Safety']
        values = [
            min(100, (details['total_revenue'] / max(kpis['avg_revenue'] * 2, 1)) * 100),
            min(100, (details['avg_mpg'] / 10) * 100),
            details['on_time_rate'] * 100,
            max(0, 100 - details['avg_idle'] * 10),
            max(0, 100 - details['incidents'] * 20)
        ]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        x = np.arange(len(categories))
        bars = ax.bar(x, values, color=['#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#e74c3c'])
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score (0-100)")
        ax.set_title(f"Performance Profile: {details['name']}")
        
        # Add value labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{val:.0f}', ha='center', fontsize=10)
        
        plt.tight_layout()
        return fig
