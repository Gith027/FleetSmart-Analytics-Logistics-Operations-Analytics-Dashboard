import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class FinancialAnalyzer:
    def __init__(self, data):
        self.data = data
        self.df = self._prepare_data()
    
    def _prepare_data(self):
        # Merge loads + trips + routes
        df = (self.data['loads']
              .merge(self.data['trips'], on='load_id', how='inner')
              .merge(self.data['routes'], on='route_id', how='left'))

        df['load_date'] = pd.to_datetime(df['load_date'])

        # Keep only 2022–2024
        df = df[df['load_date'].dt.year.between(2022, 2024)]

        # Calculate profit
        df['profit'] = df['revenue'] - df['fuel_surcharge'] - df['accessorial_charges']
        df['revenue_per_mile'] = df['revenue'] / df['actual_distance_miles'].replace(0, 1)
        df['cost_per_mile'] = (df['fuel_surcharge'] + df['accessorial_charges']) / df['actual_distance_miles'].replace(0, 1)
        df['profit_per_mile'] = df['profit'] / df['actual_distance_miles'].replace(0, 1)

        # Nice route name
        df['route_name'] = df['origin_city'].fillna('Unknown') + " → " + df['destination_city'].fillna('Unknown')

        print(f"Financial data ready: {len(df):,} trips from 2022–2024")
        return df

    def monthly_summary(self):
        m = self.df.copy()
        m['month'] = m['load_date'].dt.to_period('M')

        monthly = m.groupby('month').agg({
            'revenue': 'sum',
            'profit': 'sum',
            'actual_distance_miles': 'sum',
            'load_id': 'count'
        })

        monthly['profit_margin_%'] = (monthly['profit'] / monthly['revenue'] * 100).round(1)

        print("\nMONTHLY REVENUE & PROFIT")
        print("-" * 55)
        for month, row in monthly.iterrows():
            print(f"{month}  →  Revenue: ${row['revenue']:>10,.0f} | "
                  f"Profit: ${row['profit']:>9,.0f} | "
                  f"Margin: {row['profit_margin_%']:>5.1f}%")
        
        print(f"\nAverage Profit Margin: {monthly['profit_margin_%'].mean():.1f}%")

    def best_worst_routes(self):
        r = self.df.groupby('route_name').agg({
            'load_id': 'count',
            'profit': 'sum',
            'revenue': 'sum'
        })

        r = r[r['load_id'] >= 5]  # Only routes with 5+ trips
        r['margin_%'] = (r['profit'] / r['revenue'] * 100).round(1)

        print("\nTOP 5 MOST PROFITABLE ROUTES")
        print("-" * 65)
        for i, (route, row) in enumerate(r.nlargest(5, 'margin_%').iterrows(), 1):
            print(f"{i}. {route:<35} → {row['margin_%']:5.1f}% margin (${row['profit']:,.0f})")

        print("\nWORST 5 ROUTES (or losing money)")
        print("-" * 65)
        for i, (route, row) in enumerate(r.nsmallest(5, 'margin_%').iterrows(), 1):
            status = "LOSS" if row['profit'] < 0 else ""
            print(f"{i}. {route:<35} → {row['margin_%']:5.1f}% {status}")

    def cost_trend(self):
        daily = self.df.groupby('load_date').agg({
            'fuel_surcharge': 'sum',
            'accessorial_charges': 'sum',
            'actual_distance_miles': 'sum'
        })

        daily['total_cost'] = daily['fuel_surcharge'] + daily['accessorial_charges']
        daily['cpm'] = (daily['total_cost'] / daily['actual_distance_miles']).round(3)

        avg_cpm = daily['cpm'].mean()
        print(f"\nAverage Cost Per Mile: ${avg_cpm:.3f}")
        print(f"Highest CPM: ${daily['cpm'].max():.3f} on {daily['cpm'].idxmax().date()}")
        print(f"Lowest CPM : ${daily['cpm'].min():.3f} on {daily['cpm'].idxmin().date()}")

    def show_dashboard(self):
        print("=" * 70)
        print("        FLEETSMART FINANCIAL DASHBOARD 2022–2024")
        print("=" * 70)

        total_rev = self.df['revenue'].sum()
        total_profit = self.df['profit'].sum()
        margin = total_profit / total_rev * 100

        print(f"Total Revenue     : ${total_rev:,.0f}")
        print(f"Total Profit      : ${total_profit:,.0f}")
        print(f"Profit Margin     : {margin:.1f}%")
        print(f"Total Trips       : {len(self.df):,}")
        print(f"Total Miles       : {self.df['actual_distance_miles'].sum():,.0f}")

        self.monthly_summary()
        self.best_worst_routes()
        self.cost_trend()

        print("\n" + "="*70)
        print("ANALYSIS COMPLETE!")
        print("="*70)

    # ============== NEW STREAMLIT HELPER METHODS ==============
    
    def get_monthly_df(self, df=None):
        """Returns monthly summary as DataFrame for Streamlit tables/charts"""
        data = df if df is not None else self.df
        m = data.copy()
        m['month'] = m['load_date'].dt.to_period('M').astype(str)
        
        monthly = m.groupby('month').agg({
            'revenue': 'sum',
            'profit': 'sum',
            'actual_distance_miles': 'sum',
            'load_id': 'count'
        }).reset_index()
        
        monthly.columns = ['Month', 'Revenue', 'Profit', 'Miles', 'Trip Count']
        monthly['Profit Margin %'] = (monthly['Profit'] / monthly['Revenue'] * 100).round(1)
        monthly['Cost Per Mile'] = ((monthly['Revenue'] - monthly['Profit']) / monthly['Miles']).round(3)
        
        return monthly
    
    def get_route_stats_df(self, df=None, min_trips=5):
        """Returns all routes with statistics for filtering and display"""
        data = df if df is not None else self.df
        
        route_stats = data.groupby('route_name').agg({
            'load_id': 'count',
            'profit': 'sum',
            'revenue': 'sum',
            'actual_distance_miles': 'sum'
        }).reset_index()
        
        route_stats.columns = ['Route', 'Trip Count', 'Total Profit', 'Total Revenue', 'Total Miles']
        route_stats['Margin %'] = (route_stats['Total Profit'] / route_stats['Total Revenue'] * 100).round(1)
        route_stats['Avg Revenue/Mile'] = (route_stats['Total Revenue'] / route_stats['Total Miles']).round(2)
        
        # Filter by minimum trips
        route_stats = route_stats[route_stats['Trip Count'] >= min_trips]
        
        return route_stats.sort_values('Margin %', ascending=False)
    
    def get_worst_routes_df(self, df=None, n=5):
        """Returns bottom N underperforming routes"""
        route_stats = self.get_route_stats_df(df)
        return route_stats.nsmallest(n, 'Margin %')
    
    def get_cost_per_mile(self, df=None):
        """Returns average cost per mile for KPI display"""
        data = df if df is not None else self.df
        total_cost = data['fuel_surcharge'].sum() + data['accessorial_charges'].sum()
        total_miles = data['actual_distance_miles'].sum()
        return round(total_cost / total_miles, 3) if total_miles > 0 else 0
    
    def get_unique_routes(self):
        """Returns list of unique route names for filter dropdown"""
        return sorted(self.df['route_name'].dropna().unique().tolist())
    
    def get_date_range(self):
        """Returns min and max dates for date picker"""
        return self.df['load_date'].min(), self.df['load_date'].max()
    
    def filter_by_date(self, start_date, end_date):
        """Filters data by date range and returns filtered DataFrame"""
        mask = (self.df['load_date'] >= pd.to_datetime(start_date)) & \
               (self.df['load_date'] <= pd.to_datetime(end_date))
        return self.df[mask].copy()
    
    def filter_by_route(self, route_names, df=None):
        """Filters data by selected routes"""
        data = df if df is not None else self.df
        if not route_names or len(route_names) == 0:
            return data
        return data[data['route_name'].isin(route_names)].copy()
    
    def apply_filters(self, start_date=None, end_date=None, routes=None):
        """Apply multiple filters at once"""
        filtered = self.df.copy()
        
        if start_date and end_date:
            filtered = self.filter_by_date(start_date, end_date)
        
        if routes and len(routes) > 0:
            filtered = self.filter_by_route(routes, filtered)
        
        return filtered
    
    def get_kpis(self, df=None):
        """Returns dictionary of all KPIs for display"""
        data = df if df is not None else self.df
        
        total_revenue = data['revenue'].sum()
        total_profit = data['profit'].sum()
        margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'profit_margin': margin,
            'total_trips': len(data),
            'total_miles': data['actual_distance_miles'].sum(),
            'cost_per_mile': self.get_cost_per_mile(data),
            'avg_revenue_per_trip': total_revenue / len(data) if len(data) > 0 else 0
        }
    
    def get_alerts(self, df=None):
        """Returns list of financial alerts based on thresholds"""
        data = df if df is not None else self.df
        alerts = []
        
        # Check for loss-making routes
        route_stats = self.get_route_stats_df(data)
        loss_routes = route_stats[route_stats['Total Profit'] < 0]
        if len(loss_routes) > 0:
            alerts.append({
                'type': 'critical',
                'title': f'{len(loss_routes)} Loss-Making Routes Detected',
                'message': f"Routes losing money: {', '.join(loss_routes['Route'].head(3).tolist())}",
                'metric': f"${loss_routes['Total Profit'].sum():,.0f} total loss"
            })
        
        # Low margin routes warning
        low_margin = route_stats[route_stats['Margin %'] < 10]
        if len(low_margin) > 3:
            alerts.append({
                'type': 'warning',
                'title': f'{len(low_margin)} Routes with Low Margins (<10%)',
                'message': 'Consider reviewing pricing or costs on these routes',
                'metric': f"Avg margin: {low_margin['Margin %'].mean():.1f}%"
            })
        
        # Overall margin check
        kpis = self.get_kpis(data)
        if kpis['profit_margin'] < 15:
            alerts.append({
                'type': 'warning',
                'title': 'Overall Profit Margin Below Target',
                'message': f"Current margin is {kpis['profit_margin']:.1f}%, target is 15%+",
                'metric': f"Gap: {15 - kpis['profit_margin']:.1f}%"
            })
        
        return alerts

    def plot_monthly_trends(self, df=None):
        """Generates Monthly Revenue vs Profit Chart"""
        import matplotlib.pyplot as plt
        
        data = df if df is not None else self.df
        m = data.copy()
        m['month'] = m['load_date'].dt.to_period('M').astype(str)
        monthly = m.groupby('month')[['revenue', 'profit']].sum()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        monthly.plot(kind='bar', ax=ax, color=['#3498db', '#2ecc71'])
        ax.set_title("Monthly Revenue vs Profit")
        ax.set_ylabel("USD ($)")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        return fig

    def plot_route_profitability(self, df=None, top_n=5):
        """Generates Top N Routes Chart"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        data = df if df is not None else self.df
        route_stats = data.groupby('route_name').agg({'profit': 'sum', 'revenue': 'sum', 'load_id': 'count'})
        route_stats = route_stats[route_stats['load_id'] >= 5]
        route_stats['margin'] = (route_stats['profit'] / route_stats['revenue'] * 100)
        
        top_routes = route_stats.nlargest(top_n, 'margin')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = sns.color_palette('Greens_r', n_colors=len(top_routes))
        sns.barplot(y=top_routes.index, x=top_routes['margin'], palette=colors, ax=ax)
        ax.set_title(f"Top {top_n} Profitable Routes (Margin %)")
        ax.set_xlabel("Margin %")
        plt.tight_layout()
        return fig
    
    def plot_worst_routes(self, df=None, n=5):
        """Generates Bottom N underperforming Routes Chart"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        data = df if df is not None else self.df
        route_stats = data.groupby('route_name').agg({'profit': 'sum', 'revenue': 'sum', 'load_id': 'count'})
        route_stats = route_stats[route_stats['load_id'] >= 5]
        route_stats['margin'] = (route_stats['profit'] / route_stats['revenue'] * 100)
        
        worst_routes = route_stats.nsmallest(n, 'margin')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ['#e74c3c' if m < 0 else '#f39c12' for m in worst_routes['margin']]
        sns.barplot(y=worst_routes.index, x=worst_routes['margin'], palette=colors, ax=ax)
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax.set_title(f"Bottom {n} Underperforming Routes")
        ax.set_xlabel("Margin %")
        plt.tight_layout()
        return fig

    def plot_profit_distribution(self, df=None):
        """Risk Analysis: Profit Distribution"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        data = df if df is not None else self.df
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data['profit'], kde=True, ax=ax, color='#2ecc71', bins=30)
        
        if data['profit'].min() < 0:
            ax.axvspan(data['profit'].min(), 0, color='red', alpha=0.2, label='Loss Zone')
        
        ax.set_title("Profitability Distribution (Risk Analysis)")
        ax.set_xlabel("Profit per Trip ($)")
        ax.legend()
        plt.tight_layout()
        return fig
    
    def plot_cost_trend(self, df=None):
        """Generates Cost Per Mile trend over time"""
        import matplotlib.pyplot as plt
        
        data = df if df is not None else self.df
        
        daily = data.groupby('load_date').agg({
            'fuel_surcharge': 'sum',
            'accessorial_charges': 'sum',
            'actual_distance_miles': 'sum'
        })
        daily['cpm'] = (daily['fuel_surcharge'] + daily['accessorial_charges']) / daily['actual_distance_miles']
        
        # Resample to weekly for smoother trend
        weekly = daily['cpm'].resample('W').mean()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(weekly.index, weekly.values, color='#e74c3c', linewidth=2)
        ax.fill_between(weekly.index, weekly.values, alpha=0.3, color='#e74c3c')
        ax.axhline(y=weekly.mean(), color='#3498db', linestyle='--', label=f'Avg: ${weekly.mean():.3f}')
        ax.set_title("Cost Per Mile Trend (Weekly Average)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cost Per Mile ($)")
        ax.legend()
        plt.tight_layout()
        return fig

