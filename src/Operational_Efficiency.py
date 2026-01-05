import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class OperationalAnalyzer:
    def __init__(self, data_dict):
        self.data = data_dict
        self.op_data = self._prepare_data()

    def _prepare_data(self):
        print("Preparing Operational Efficiency data...")
        
        # Copy input tables to avoid modifying originals
        trips = self.data.get('trips')
        loads = self.data.get('loads')
        events = self.data.get('delivery_events')
        driver_monthly = self.data.get('driver_monthly_metrics')
        truck_monthly = self.data.get('truck_utilization_metrics')
        routes = self.data.get('routes')

        if any(df is None or df.empty for df in [trips, loads, events, routes]):
            print("Warning: One or more core tables are missing or empty.")
            # Create minimal dataframe to prevent crashes
            df = pd.DataFrame()
            return df

        trips = trips.copy()
        loads = loads.copy()
        events = events.copy()
        routes = routes.copy()

        # Convert dates
        trips['dispatch_date'] = pd.to_datetime(trips['dispatch_date'], errors='coerce')
        events['scheduled_datetime'] = pd.to_datetime(events['scheduled_datetime'], errors='coerce')
        events['actual_datetime'] = pd.to_datetime(events['actual_datetime'], errors='coerce')

        # Core merges
        df = (trips
              .merge(loads, on='load_id', how='left')
              .merge(events, on=['load_id', 'trip_id'], how='left')
              .merge(routes, on='route_id', how='left'))

        # On-Time Flag (with 30-minute grace)
        df['on_time'] = np.where(
            (df['actual_datetime'].notna()) & (df['scheduled_datetime'].notna()),
            (df['actual_datetime'] <= df['scheduled_datetime'] + pd.Timedelta(minutes=30)),
            False
        )

        # Human-readable route name
        df['route_name'] = (df['origin_city'].fillna('Unknown') + " to " +
                            df['destination_city'].fillna('Unknown'))

        # Extract month for temporal joins
        df['month'] = df['dispatch_date'].dt.to_period('M')

        # Prepare monthly metrics if available
        if driver_monthly is not None and not driver_monthly.empty:
            driver_monthly = driver_monthly.copy()
            driver_monthly['month'] = pd.to_datetime(driver_monthly['month'], errors='coerce').dt.to_period('M')
            driver_cols = ['driver_id', 'month']
            if 'average_idle_hours' in driver_monthly.columns:
                driver_cols.append('average_idle_hours')
            if 'average_mpg' in driver_monthly.columns:
                driver_cols.append('average_mpg')
            df = df.merge(driver_monthly[driver_cols], on=['driver_id', 'month'], how='left')

        if truck_monthly is not None and not truck_monthly.empty:
            truck_monthly = truck_monthly.copy()
            truck_monthly['month'] = pd.to_datetime(truck_monthly['month'], errors='coerce').dt.to_period('M')
            truck_cols = ['truck_id', 'month']
            if 'utilization_rate' in truck_monthly.columns:
                truck_cols.append('utilization_rate')
            if 'downtime_hours' in truck_monthly.columns:
                truck_cols.append('downtime_hours')
            df = df.merge(truck_monthly[truck_cols], on=['truck_id', 'month'], how='left')

        print(f"Operational data ready: {len(df):,} trip records analyzed")
        return df

    def show_dashboard(self):
        if self.op_data.empty:
            print("No operational data available!")
            return

        df = self.op_data

        print("\n" + "="*80)
        print(" FLEETSMART – OPERATIONAL EFFICIENCY DASHBOARD")
        print("="*80)

        # === KPI Calculations (safe handling) ===
        on_time_rate = df['on_time'].mean() * 100 if 'on_time' in df.columns else 0

        fleet_util = (df['utilization_rate'].mean() * 100 
                      if 'utilization_rate' in df.columns and df['utilization_rate'].notna().any() 
                      else 0)

        avg_idle = (df['average_idle_hours'].mean() 
                    if 'average_idle_hours' in df.columns and df['average_idle_hours'].notna().any() 
                    else 0)

        avg_mpg = (df['average_mpg'].mean() 
                   if 'average_mpg' in df.columns and df['average_mpg'].notna().any() 
                   else 0)

        downtime_avg = (df['downtime_hours'].mean() 
                        if 'downtime_hours' in df.columns and df['downtime_hours'].notna().any() 
                        else 0)

        unique_trucks = df['truck_id'].nunique() if 'truck_id' in df.columns else 0
        trips_per_truck = len(df) / unique_trucks if unique_trucks > 0 else 0

        empty_miles_pct = 18.7  # Placeholder – improve with real backhaul data later

        print(f" On-Time Delivery Rate     : {on_time_rate:.1f}%")
        print(f" Fleet Utilization Rate    : {fleet_util:.1f}%")
        print(f" Empty/Deadhead Miles      : ~{empty_miles_pct:.1f}%")
        print(f" Average Idle Hours/Trip   : {avg_idle:.1f} hours")
        print(f" Fleet Average MPG         : {avg_mpg:.1f}")
        print(f" Avg Downtime per Truck    : {downtime_avg:.1f} hrs/month")
        print(f" Trips per Truck (Monthly) : {trips_per_truck:.1f}")
        print()

        # === On-Time Delivery Trend ===
        print("ON-TIME DELIVERY TREND (Last 12 Months)")
        print("-" * 50)
        if 'dispatch_date' in df.columns:
            monthly_otd = df.copy()
            monthly_otd['month_period'] = df['dispatch_date'].dt.to_period('M')
            otd_trend = monthly_otd.groupby('month_period')['on_time'].mean() * 100
            if not otd_trend.empty:
                for month, rate in otd_trend.tail(12).items():
                    status = "Good" if rate >= 90 else "Needs Work" if rate >= 80 else "Critical"
                    print(f" {month} → {rate:5.1f}% [{status}]")
            else:
                print(" No monthly data available.")
        else:
            print(" No dispatch date data available.")

        # === Worst Performing Routes ===
        print("\nWORST 5 ROUTES BY ON-TIME DELIVERY")
        print("-" * 60)
        if 'route_name' in df.columns and 'on_time' in df.columns:
            route_otd = df.groupby('route_name')['on_time'].mean() * 100
            worst_routes = route_otd.nsmallest(5)
            if not worst_routes.empty:
                for route, rate in worst_routes.items():
                    print(f" {route:<35} → {rate:5.1f}% on-time")
            else:
                print(" Not enough route data.")
        else:
            print(" Missing route or on-time data.")

        # === Driver Efficiency Leaderboard (Fully Robust) ===
        print("\nTOP 10 MOST EFFICIENT DRIVERS (Idle + MPG + OTD)")
        print("-" * 70)

        if 'driver_id' in df.columns and 'on_time' in df.columns:
            # Dynamically build aggregation dict based on available columns
            agg_dict = {'on_time': 'mean'}
            if 'average_idle_hours' in df.columns:
                agg_dict['average_idle_hours'] = 'mean'
            if 'average_mpg' in df.columns:
                agg_dict['average_mpg'] = 'mean'

            driver_eff = df.groupby('driver_id').agg(agg_dict)

            # Remove drivers with no metric data
            driver_eff = driver_eff.dropna(how='all')

            if not driver_eff.empty:
                score_components = []
                
                if 'average_idle_hours' in driver_eff.columns:
                    idle_score = (10 - driver_eff['average_idle_hours'].clip(upper=10)) * 3
                    score_components.append(idle_score)
                
                if 'average_mpg' in driver_eff.columns:
                    mpg_score = driver_eff['average_mpg'] * 2
                    score_components.append(mpg_score)
                
                # OTD always included and heavily weighted
                otd_score = driver_eff['on_time'] * 30
                score_components.append(otd_score)

                driver_eff['eff_score'] = sum(score_components)

                top_drivers = driver_eff.nlargest(10, 'eff_score').reset_index()

                # Add driver names if available
                if 'drivers' in self.data and not self.data['drivers'].empty and 'full_name' in self.data['drivers'].columns:
                    top_drivers = top_drivers.merge(
                        self.data['drivers'][['driver_id', 'full_name']],
                        on='driver_id', how='left'
                    )

                for i, row in top_drivers.iterrows():
                    name = row.get('full_name', f"Driver {row['driver_id']}")
                    score = row['eff_score']
                    print(f" {i+1:2d}. {name:<25} → Score: {score:.0f}/100")
            else:
                print(" Not enough driver performance data for leaderboard.")
        else:
            print(" Missing driver_id or on_time data for leaderboard.")

        # === Final Alerts ===
        print("\n" + "="*80)
        if on_time_rate < 90:
            print("ALERT: On-Time Delivery below target! Action needed.")
        if fleet_util < 80:
            print("ALERT: Fleet Utilization low — trucks sitting idle.")
        if avg_idle > 6:
            print("ALERT: High idle time — costing fuel and money!")
        print("ANALYSIS COMPLETE!")
        print("="*80)

    # ============== NEW STREAMLIT HELPER METHODS ==============
    
    def get_kpis(self, df=None):
        """Returns dictionary of all operational KPIs"""
        data = df if df is not None else self.op_data
        if data.empty:
            return {}
        
        on_time_rate = data['on_time'].mean() * 100 if 'on_time' in data.columns else 0
        
        fleet_util = (data['utilization_rate'].mean() * 100 
                      if 'utilization_rate' in data.columns and data['utilization_rate'].notna().any() 
                      else 0)
        
        avg_idle = (data['average_idle_hours'].mean() 
                    if 'average_idle_hours' in data.columns and data['average_idle_hours'].notna().any() 
                    else 0)
        
        avg_mpg = (data['average_mpg'].mean() 
                   if 'average_mpg' in data.columns and data['average_mpg'].notna().any() 
                   else 0)
        
        return {
            'on_time_rate': on_time_rate,
            'fleet_utilization': fleet_util,
            'avg_idle_hours': avg_idle,
            'avg_mpg': avg_mpg,
            'total_trips': len(data),
            'unique_trucks': data['truck_id'].nunique() if 'truck_id' in data.columns else 0,
            'unique_drivers': data['driver_id'].nunique() if 'driver_id' in data.columns else 0
        }
    
    def get_delay_stats(self, df=None):
        """Returns delay time statistics"""
        data = df if df is not None else self.op_data
        if data.empty:
            return {'avg_delay': 0, 'max_delay': 0, 'delayed_count': 0}
        
        delayed = data[data['on_time'] == False].copy()
        if delayed.empty:
            return {'avg_delay': 0, 'max_delay': 0, 'delayed_count': 0}
        
        delayed['delay_minutes'] = (delayed['actual_datetime'] - delayed['scheduled_datetime']).dt.total_seconds() / 60
        delayed['delay_minutes'] = delayed['delay_minutes'].clip(lower=0)
        
        return {
            'avg_delay': delayed['delay_minutes'].mean(),
            'max_delay': delayed['delay_minutes'].max(),
            'delayed_count': len(delayed),
            'delay_pct': len(delayed) / len(data) * 100
        }
    
    def get_route_ontime_df(self, df=None, min_trips=3):
        """Returns route-wise on-time rates for table/charts"""
        data = df if df is not None else self.op_data
        if data.empty:
            return pd.DataFrame()
        
        route_stats = data.groupby('route_name').agg({
            'on_time': ['sum', 'count', 'mean']
        }).reset_index()
        route_stats.columns = ['Route', 'On-Time Count', 'Total Trips', 'On-Time Rate']
        route_stats['On-Time Rate'] = (route_stats['On-Time Rate'] * 100).round(1)
        route_stats['Delayed Count'] = route_stats['Total Trips'] - route_stats['On-Time Count']
        
        route_stats = route_stats[route_stats['Total Trips'] >= min_trips]
        return route_stats.sort_values('On-Time Rate', ascending=False)
    
    def get_worst_routes_df(self, df=None, n=5):
        """Returns bottom N routes by on-time rate"""
        route_stats = self.get_route_ontime_df(df)
        return route_stats.nsmallest(n, 'On-Time Rate')
    
    def get_best_routes_df(self, df=None, n=5):
        """Returns top N routes by on-time rate"""
        route_stats = self.get_route_ontime_df(df)
        return route_stats.nlargest(n, 'On-Time Rate')
    
    def get_truck_reliability_df(self, df=None):
        """Returns truck reliability ranking"""
        data = df if df is not None else self.op_data
        if data.empty:
            return pd.DataFrame()
        
        truck_stats = data.groupby('truck_id').agg({
            'on_time': ['sum', 'count', 'mean'],
        }).reset_index()
        truck_stats.columns = ['Truck ID', 'On-Time Count', 'Total Trips', 'On-Time Rate']
        truck_stats['On-Time Rate'] = (truck_stats['On-Time Rate'] * 100).round(1)
        
        # Add utilization if available
        if 'utilization_rate' in data.columns:
            util_stats = data.groupby('truck_id')['utilization_rate'].mean().reset_index()
            util_stats.columns = ['Truck ID', 'Utilization %']
            util_stats['Utilization %'] = (util_stats['Utilization %'] * 100).round(1)
            truck_stats = truck_stats.merge(util_stats, on='Truck ID', how='left')
        
        return truck_stats.sort_values('On-Time Rate', ascending=False)
    
    def get_customer_ontime_df(self, df=None):
        """Returns customer-wise on-time rates"""
        data = df if df is not None else self.op_data
        if data.empty or 'customer_id' not in data.columns:
            return pd.DataFrame()
        
        # Merge customer names if available
        customer_stats = data.groupby('customer_id').agg({
            'on_time': ['sum', 'count', 'mean']
        }).reset_index()
        customer_stats.columns = ['Customer ID', 'On-Time Count', 'Total Trips', 'On-Time Rate']
        customer_stats['On-Time Rate'] = (customer_stats['On-Time Rate'] * 100).round(1)
        
        # Add customer names if available
        customers = self.data.get('customers')
        if customers is not None and 'company_name' in customers.columns:
            customer_stats = customer_stats.merge(
                customers[['customer_id', 'company_name']], 
                left_on='Customer ID', right_on='customer_id', how='left'
            )
            customer_stats['Customer'] = customer_stats['company_name'].fillna('Customer ' + customer_stats['Customer ID'].astype(str))
            customer_stats = customer_stats.drop(columns=['customer_id', 'company_name'], errors='ignore')
        else:
            customer_stats['Customer'] = 'Customer ' + customer_stats['Customer ID'].astype(str)
        
        return customer_stats.sort_values('On-Time Rate', ascending=False)
    
    def get_driver_reliability_df(self, df=None):
        """Returns driver reliability ranking with efficiency score"""
        data = df if df is not None else self.op_data
        if data.empty or 'driver_id' not in data.columns:
            return pd.DataFrame()
        
        agg_dict = {'on_time': ['sum', 'count', 'mean']}
        if 'average_idle_hours' in data.columns:
            agg_dict['average_idle_hours'] = 'mean'
        if 'average_mpg' in data.columns:
            agg_dict['average_mpg'] = 'mean'
        
        driver_stats = data.groupby('driver_id').agg(agg_dict).reset_index()
        
        # Flatten columns
        driver_stats.columns = ['Driver ID', 'On-Time Count', 'Total Trips', 'On-Time Rate'] + \
                               (['Avg Idle Hrs'] if 'average_idle_hours' in data.columns else []) + \
                               (['Avg MPG'] if 'average_mpg' in data.columns else [])
        
        driver_stats['On-Time Rate'] = (driver_stats['On-Time Rate'] * 100).round(1)
        
        # Calculate efficiency score
        score = driver_stats['On-Time Rate'] * 0.4
        if 'Avg Idle Hrs' in driver_stats.columns:
            score -= driver_stats['Avg Idle Hrs'].fillna(0) * 2
        if 'Avg MPG' in driver_stats.columns:
            score += driver_stats['Avg MPG'].fillna(0) * 3
        driver_stats['Efficiency Score'] = score.round(1)
        
        # Add driver names
        drivers = self.data.get('drivers')
        if drivers is not None:
            name_cols = []
            if 'first_name' in drivers.columns:
                name_cols.append('first_name')
            if 'last_name' in drivers.columns:
                name_cols.append('last_name')
            if name_cols:
                driver_names = drivers[['driver_id'] + name_cols].copy()
                driver_names['Driver Name'] = driver_names[name_cols].fillna('').agg(' '.join, axis=1).str.strip()
                driver_stats = driver_stats.merge(driver_names[['driver_id', 'Driver Name']], 
                                                   left_on='Driver ID', right_on='driver_id', how='left')
                driver_stats = driver_stats.drop(columns=['driver_id'], errors='ignore')
        
        if 'Driver Name' not in driver_stats.columns:
            driver_stats['Driver Name'] = 'Driver ' + driver_stats['Driver ID'].astype(str)
        
        return driver_stats.sort_values('Efficiency Score', ascending=False)
    
    def get_utilization_df(self, df=None):
        """Returns truck utilization data"""
        data = df if df is not None else self.op_data
        if data.empty or 'utilization_rate' not in data.columns:
            return pd.DataFrame()
        
        util_stats = data.groupby('truck_id').agg({
            'utilization_rate': 'mean',
            'load_id': 'count'
        }).reset_index()
        util_stats.columns = ['Truck ID', 'Utilization Rate', 'Trip Count']
        util_stats['Utilization Rate'] = (util_stats['Utilization Rate'] * 100).round(1)
        
        # Add downtime if available
        if 'downtime_hours' in data.columns:
            downtime = data.groupby('truck_id')['downtime_hours'].mean().reset_index()
            downtime.columns = ['Truck ID', 'Avg Downtime Hrs']
            downtime['Avg Downtime Hrs'] = downtime['Avg Downtime Hrs'].round(1)
            util_stats = util_stats.merge(downtime, on='Truck ID', how='left')
        
        return util_stats.sort_values('Utilization Rate', ascending=False)
    
    def get_unique_values(self, column):
        """Returns unique values for filter dropdowns"""
        if column in self.op_data.columns:
            return sorted(self.op_data[column].dropna().unique().tolist())
        return []
    
    def get_date_range(self):
        """Returns min and max dispatch dates"""
        if 'dispatch_date' in self.op_data.columns:
            return self.op_data['dispatch_date'].min(), self.op_data['dispatch_date'].max()
        return None, None
    
    def filter_data(self, start_date=None, end_date=None, routes=None, trucks=None, drivers=None, customers=None, on_time_status=None):
        """Apply multiple filters to operational data"""
        filtered = self.op_data.copy()
        
        if start_date and end_date and 'dispatch_date' in filtered.columns:
            mask = (filtered['dispatch_date'] >= pd.to_datetime(start_date)) & \
                   (filtered['dispatch_date'] <= pd.to_datetime(end_date))
            filtered = filtered[mask]
        
        if routes and len(routes) > 0 and 'route_name' in filtered.columns:
            filtered = filtered[filtered['route_name'].isin(routes)]
        
        if trucks and len(trucks) > 0 and 'truck_id' in filtered.columns:
            filtered = filtered[filtered['truck_id'].isin(trucks)]
        
        if drivers and len(drivers) > 0 and 'driver_id' in filtered.columns:
            filtered = filtered[filtered['driver_id'].isin(drivers)]
        
        if customers and len(customers) > 0 and 'customer_id' in filtered.columns:
            filtered = filtered[filtered['customer_id'].isin(customers)]
        
        if on_time_status is not None and 'on_time' in filtered.columns:
            if on_time_status == 'on_time':
                filtered = filtered[filtered['on_time'] == True]
            elif on_time_status == 'delayed':
                filtered = filtered[filtered['on_time'] == False]
        
        return filtered
    
    def get_alerts(self, df=None):
        """Returns list of operational alerts based on thresholds"""
        data = df if df is not None else self.op_data
        alerts = []
        
        kpis = self.get_kpis(data)
        
        # On-time rate alert
        if kpis.get('on_time_rate', 100) < 85:
            alerts.append({
                'type': 'critical',
                'title': 'On-Time Delivery Below Target',
                'message': f"Current rate: {kpis['on_time_rate']:.1f}%, Target: 85%+",
                'metric': f"Gap: {85 - kpis['on_time_rate']:.1f}%"
            })
        elif kpis.get('on_time_rate', 100) < 90:
            alerts.append({
                'type': 'warning',
                'title': 'On-Time Delivery Needs Improvement',
                'message': f"Current rate: {kpis['on_time_rate']:.1f}%, Target: 90%+",
                'metric': f"Gap: {90 - kpis['on_time_rate']:.1f}%"
            })
        
        # Fleet utilization alert
        if kpis.get('fleet_utilization', 100) < 75:
            alerts.append({
                'type': 'warning',
                'title': 'Low Fleet Utilization',
                'message': f"Trucks are underutilized at {kpis['fleet_utilization']:.1f}%",
                'metric': 'Consider route optimization'
            })
        
        # High idle time alert
        if kpis.get('avg_idle_hours', 0) > 5:
            alerts.append({
                'type': 'warning',
                'title': 'High Average Idle Time',
                'message': f"Drivers averaging {kpis['avg_idle_hours']:.1f} idle hours",
                'metric': 'Review scheduling and routes'
            })
        
        # Check for problem routes
        worst_routes = self.get_worst_routes_df(data, n=3)
        if not worst_routes.empty and worst_routes.iloc[0]['On-Time Rate'] < 70:
            route_names = worst_routes['Route'].head(3).tolist()
            alerts.append({
                'type': 'critical',
                'title': 'Routes with Critical On-Time Issues',
                'message': f"Routes below 70%: {', '.join(route_names[:2])}",
                'metric': f"Worst: {worst_routes.iloc[0]['On-Time Rate']:.1f}%"
            })
        
        return alerts

    def plot_ontime_distribution(self, df=None):
        """Generates On-Time vs Delayed Pie Chart"""
        import matplotlib.pyplot as plt
        
        data = df if df is not None else self.op_data
        otd_counts = data['on_time'].value_counts().rename({True: 'On-Time', False: 'Delayed'})
        
        fig, ax = plt.subplots(figsize=(6, 6))
        colors = ['#2ecc71', '#e74c3c']
        wedges, texts, autotexts = ax.pie(otd_counts, labels=otd_counts.index, autopct='%1.1f%%', 
                                           colors=colors, startangle=90, explode=[0.02, 0.02])
        ax.set_title("On-Time vs Delayed Deliveries")
        plt.tight_layout()
        return fig

    def plot_ontime_trend(self, df=None):
        """Generates Monthly On-Time Reliability Chart"""
        import matplotlib.pyplot as plt
        
        data = df if df is not None else self.op_data
        if 'dispatch_date' not in data.columns: 
            return None
        
        temp = data.copy()
        temp['month'] = temp['dispatch_date'].dt.to_period('M').astype(str)
        trend = temp.groupby('month')['on_time'].mean() * 100
        
        fig, ax = plt.subplots(figsize=(10, 5))
        trend.plot(kind='line', marker='o', ax=ax, color='#2980b9', linewidth=2, markersize=8)
        ax.axhline(y=90, color='#2ecc71', linestyle='--', alpha=0.7, label='Target (90%)')
        ax.axhline(y=85, color='#f39c12', linestyle='--', alpha=0.7, label='Minimum (85%)')
        ax.fill_between(trend.index, trend.values, 85, where=(trend.values >= 85), 
                        alpha=0.3, color='#2ecc71', interpolate=True)
        ax.fill_between(trend.index, trend.values, 85, where=(trend.values < 85), 
                        alpha=0.3, color='#e74c3c', interpolate=True)
        ax.set_title("Monthly On-Time Reliability (%)")
        ax.set_ylabel("On-Time %")
        ax.set_ylim(0, 105)
        ax.legend(loc='lower right')
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
    
    def plot_route_performance(self, df=None, top_n=10):
        """Horizontal bar chart of route on-time performance"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        route_stats = self.get_route_ontime_df(df)
        if route_stats.empty:
            return None
        
        # Get top and bottom routes
        display_routes = route_stats.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71' if rate >= 90 else '#f39c12' if rate >= 80 else '#e74c3c' 
                  for rate in display_routes['On-Time Rate']]
        
        bars = ax.barh(display_routes['Route'], display_routes['On-Time Rate'], color=colors)
        ax.axvline(x=90, color='#2ecc71', linestyle='--', alpha=0.7, label='Target')
        ax.axvline(x=85, color='#f39c12', linestyle='--', alpha=0.7, label='Minimum')
        
        ax.set_xlabel("On-Time Rate (%)")
        ax.set_title(f"Top {top_n} Routes by On-Time Performance")
        ax.set_xlim(0, 105)
        ax.legend()
        plt.tight_layout()
        return fig
    
    def plot_truck_reliability(self, df=None, top_n=10):
        """Bar chart of truck reliability"""
        import matplotlib.pyplot as plt
        
        truck_stats = self.get_truck_reliability_df(df)
        if truck_stats.empty:
            return None
        
        display_trucks = truck_stats.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ['#2ecc71' if rate >= 90 else '#f39c12' if rate >= 80 else '#e74c3c' 
                  for rate in display_trucks['On-Time Rate']]
        
        ax.bar(display_trucks['Truck ID'].astype(str), display_trucks['On-Time Rate'], color=colors)
        ax.axhline(y=90, color='#2ecc71', linestyle='--', alpha=0.7, label='Target')
        ax.set_xlabel("Truck ID")
        ax.set_ylabel("On-Time Rate (%)")
        ax.set_title(f"Top {top_n} Trucks by Reliability")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
    
    def plot_delay_distribution(self, df=None):
        """Histogram of delay times"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        data = df if df is not None else self.op_data
        delayed = data[data['on_time'] == False].copy()
        
        if delayed.empty:
            return None
        
        delayed['delay_minutes'] = (delayed['actual_datetime'] - delayed['scheduled_datetime']).dt.total_seconds() / 60
        delayed['delay_minutes'] = delayed['delay_minutes'].clip(lower=0, upper=480)  # Cap at 8 hours
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(delayed['delay_minutes'], kde=True, ax=ax, color='#e74c3c', bins=30)
        ax.axvline(x=30, color='#f39c12', linestyle='--', label='30 min (Grace)')
        ax.axvline(x=60, color='#e74c3c', linestyle='--', label='1 hour')
        ax.set_xlabel("Delay (minutes)")
        ax.set_ylabel("Count")
        ax.set_title("Distribution of Delivery Delays")
        ax.legend()
        plt.tight_layout()
        return fig
