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


