# predictive_insights.py - Multi-Page Dashboard (3 pages, 4 charts each)
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class PredictiveInsights:
    def __init__(self, processed_data):
        self.data = processed_data
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (20, 12)
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.titleweight'] = 'bold'

    def create_page(self, page_num, title):
        fig = plt.figure(figsize=(24, 14))
        fig.suptitle(f"FleetSmart Analytics - Page {page_num}: {title}", fontsize=24, fontweight='bold', y=0.98)
        gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4)
        return fig, gs

    def show_insights(self):
        print("\n" + "="*100)
        print("          FLEETSMART MULTI-PAGE PREDICTIVE DASHBOARD")
        print("="*100)
        print("You will see 3 separate dashboard pages. Close each window to see the next.\n")

        loads = self.data.get('loads')
        trips = self.data.get('trips')
        maint = self.data.get('maintenance_records')
        fuel = self.data.get('fuel_purchases')
        driver_monthly = self.data.get('driver_monthly_metrics')
        drivers = self.data.get('drivers')

        if loads is None:
            print("Missing loads data!")
            return

        # Prepare common data
        loads = loads.copy()
        loads['load_date'] = pd.to_datetime(loads['load_date'], errors='coerce')
        loads['month'] = loads['load_date'].dt.to_period('M')
        monthly_loads = loads.groupby('month').size().sort_index()

        # ==================== PAGE 1: Demand & Volume ====================
        fig1, gs1 = self.create_page(1, "Demand & Load Volume Analysis")

        ax1 = fig1.add_subplot(gs1[0, 0])
        last_12 = monthly_loads.tail(12)
        bars = ax1.bar(last_12.index.astype(str), last_12.values, color='#3498db')
        ax1.set_title('Monthly Load Volume (Last 12 Months)')
        ax1.set_ylabel('Number of Loads')
        ax1.tick_params(axis='x', rotation=45)
        for bar in bars:
            h = int(bar.get_height())
            ax1.text(bar.get_x() + bar.get_width()/2, h + 10, h, ha='center', fontweight='bold')

        ax2 = fig1.add_subplot(gs1[0, 1])
        monthly_loads.plot(linewidth=3, marker='o', ax=ax2, color='#2ecc71')
        ax2.set_title('Load Volume Trend Over Time')
        ax2.set_ylabel('Loads')
        ax2.tick_params(axis='x', rotation=45)

        ax3 = fig1.add_subplot(gs1[1, :])
        growth = monthly_loads.pct_change().fillna(0) * 100
        growth.plot(kind='bar', ax=ax3, color=np.where(growth > 0, 'green', 'red'))
        ax3.set_title('Monthly Growth Rate (%)')
        ax3.set_ylabel('Growth %')
        ax3.tick_params(axis='x', rotation=45)

        plt.show()  # Page 1

        # ==================== PAGE 2: Maintenance & Fuel ====================
        fig2, gs2 = self.create_page(2, "Maintenance & Fuel Efficiency")

        ax1 = fig2.add_subplot(gs2[0, 0])
        if maint is not None and not maint.empty:
            maint_by_truck = maint.groupby('truck_id').size().sort_values(ascending=False).head(10)
            maint_by_truck.plot(kind='barh', ax=ax1, color='#e74c3c')
            ax1.set_title('Top 10 Trucks by Maintenance Events')
            ax1.set_xlabel('Events')
            ax1.invert_yaxis()
        else:
            ax1.text(0.5, 0.5, 'No Maintenance Data', transform=ax1.transAxes, ha='center', fontsize=20)

        ax2 = fig2.add_subplot(gs2[0, 1])
        if fuel is not None and not fuel.empty:
            fuel['purchase_date'] = pd.to_datetime(fuel['purchase_date'], errors='coerce')
            fuel['month'] = fuel['purchase_date'].dt.to_period('M')
            monthly_fuel = fuel.groupby('month')['total_cost'].sum()
            monthly_fuel.plot(kind='line', marker='o', ax=ax2, color='#f39c12', linewidth=3)
            ax2.set_title('Monthly Fuel Cost Trend')
            ax2.set_ylabel('Total Cost ($)')
        else:
            ax2.text(0.5, 0.5, 'No Fuel Data', transform=ax2.transAxes, ha='center', fontsize=20)

        ax3 = fig2.add_subplot(gs2[1, :])
        ax3.text(0.5, 0.5, 'Fuel & Maintenance Summary\n\n• Monitor high-maintenance trucks\n• Track rising fuel costs\n• Schedule preventive maintenance',
                 transform=ax3.transAxes, ha='center', va='center', fontsize=18,
                 bbox=dict(facecolor='lightyellow', edgecolor='orange', boxstyle='round,pad=1'))
        ax3.axis('off')
        ax3.set_title('Key Recommendations', fontsize=18)

        plt.show()  # Page 2

        # ==================== PAGE 3: Driver Performance ====================
        fig3, gs3 = self.create_page(3, "Driver Performance Insights")

        if driver_monthly is not None and drivers is not None:
            df_drv = driver_monthly.copy()
            for col in ['total_revenue', 'average_mpg', 'on_time_delivery_rate', 'average_idle_hours']:
                if col in df_drv.columns:
                    df_drv[col] = pd.to_numeric(df_drv[col], errors='coerce')

            df_drv = df_drv.merge(drivers[['driver_id', 'first_name', 'last_name']], on='driver_id', how='left')
            df_drv['name'] = df_drv['first_name'].fillna('') + " " + df_drv['last_name'].fillna('')

            ax1 = fig3.add_subplot(gs3[0, 0])
            top_rev = df_drv.nlargest(10, 'total_revenue')
            ax1.barh(top_rev['name'], top_rev['total_revenue'], color='#9b59b6')
            ax1.set_title('Top 10 Drivers by Revenue')
            ax1.invert_yaxis()

            ax2 = fig3.add_subplot(gs3[0, 1])
            sizes = df_drv['on_time_delivery_rate'].fillna(0.5) * 400 + 100
            scatter = ax2.scatter(df_drv['average_mpg'], df_drv['total_revenue'],
                                  s=sizes, c=df_drv['average_idle_hours'], cmap='coolwarm', alpha=0.8)
            ax2.set_title('Revenue vs MPG\n(Bubble = On-Time Rate)')
            ax2.set_xlabel('MPG')
            ax2.set_ylabel('Revenue ($)')
            plt.colorbar(scatter, ax=ax2, label='Idle Hours')

            ax3 = fig3.add_subplot(gs3[1, :])
            ax3.axis('off')
            ax3.text(0.5, 0.5, 'DRIVER INSIGHTS\n\n• Reward top revenue drivers\n• Train low MPG / high idle drivers\n• Focus on on-time delivery leaders',
                     transform=ax3.transAxes, ha='center', va='center', fontsize=18,
                     bbox=dict(facecolor='lightblue', edgecolor='blue', boxstyle='round,pad=1'))
            ax3.set_title('Action Recommendations', fontsize=18)

        plt.show()  # Page 3

        print("All 3 dashboard pages displayed successfully!")
        print("Close each window to continue to the next page.")
        print("="*100)