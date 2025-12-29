# predictive_insights.py
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class PredictiveInsights:
    def __init__(self, processed_data):
        self.data = processed_data
        print("Predictive Insights ready!")

    def show_insights(self):
        print("\n" + "="*80)
        print(" PREDICTIVE INSIGHTS & VISUALIZATIONS")
        print("="*80)

        loads = self.data.get('loads')
        trips = self.data.get('trips')
        maint = self.data.get('maintenance_records')

        if loads is None or trips is None:
            print("Missing loads or trips data!")
            return

        # 1. Monthly Load Trend
        if 'load_date' in loads.columns:
            loads['month'] = loads['load_date'].dt.to_period('M')
            monthly_loads = loads.groupby('month').size()

            print("MONTHLY LOAD VOLUME TREND")
            print("-" * 40)
            print(monthly_loads.tail(12))

            # Simple plot
            plt.figure(figsize=(10, 4))
            monthly_loads.tail(12).plot(kind='bar', color='skyblue')
            plt.title("Loads per Month (Last 12 Months)")
            plt.ylabel("Number of Loads")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        # 2. Maintenance Prediction Insight
        if maint is not None and 'truck_id' in maint.columns:
            maint_count = maint.groupby('truck_id').size()
            high_maint_trucks = maint_count[maint_count > maint_count.quantile(0.8)]
            print(f"\nHIGH MAINTENANCE RISK TRUCKS ({len(high_maint_trucks)} trucks need attention):")
            print(high_maint_trucks)

        # 3. Simple Forecast Message
        recent_growth = monthly_loads.pct_change().mean() * 100 if len(monthly_loads) > 1 else 0
        print(f"\nINSIGHT: Load volume growing by ~{recent_growth:.1f}% per month on average.")
        if recent_growth > 5:
            print("RECOMMENDATION: Plan for more drivers/trucks soon!")
        else:
            print("RECOMMENDATION: Current capacity seems sufficient.")

        print("\nPREDICTIVE INSIGHTS COMPLETE!")
        print("="*80)