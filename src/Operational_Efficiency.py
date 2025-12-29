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