import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

class FinancialAnalyzer:
    def __init__(self, processed_data: Dict[str, pd.DataFrame]):
        
        self.data = processed_data  #Stores the cleaned datasets
        
        # Sets analysis period: 3 full years (2022–2024)
        self.start_date = pd.Timestamp('2022-01-01')
        self.end_date = pd.Timestamp('2024-12-31')
        
        # Initialize main merged dataset
        self.merged_data = None
        self._prepare_merged_data()
        
    
    def _prepare_merged_data(self):
        try:
            # 1. Merge loads with trips (Joins loads and trips tables on load_id → only matched records kept)
            financial_data = pd.merge(
                self.data['loads'],
                self.data['trips'],
                left_on='load_id',
                right_on='load_id',
                how='inner',
                suffixes=('_load', '_trip')
            )
            
            
            # 2. Add route information
            financial_data = pd.merge(
                financial_data,
                self.data['routes'][['route_id', 'origin_city', 'origin_state', 
                                    'destination_city', 'destination_state', 
                                    'typical_distance_miles', 'base_rate_per_mile']],
                left_on='route_id',
                right_on='route_id',
                how='left'
            )
            
            # 3. Calculate derived metrics
            financial_data['load_date'] = pd.to_datetime(financial_data['load_date'])
            #Calculates true profit = revenue minus variable costs
            financial_data['profit'] = financial_data['revenue'] - financial_data['fuel_surcharge'] - financial_data['accessorial_charges']
            financial_data['revenue_per_mile'] = financial_data['revenue'] / financial_data['actual_distance_miles'].replace(0, np.nan)
            financial_data['profit_per_mile'] = financial_data['profit'] / financial_data['actual_distance_miles'].replace(0, np.nan)
            financial_data['cost_per_mile'] = (financial_data['fuel_surcharge'] + financial_data['accessorial_charges']) / financial_data['actual_distance_miles'].replace(0, np.nan)
            
            # Filters to 2022–2024 only
            financial_data = financial_data[
                (financial_data['load_date'] >= self.start_date) & 
                (financial_data['load_date'] <= self.end_date)
            ]
            
            self.merged_data = financial_data
            print(f"Financial dataset prepared: {self.merged_data.shape[0]:,} records")
            
        except Exception as e:
            print(f"Error preparing financial data: {e}")
            self.merged_data = pd.DataFrame()
    
    def revenue_vs_cost_analysis(self, period: str = 'monthly') -> pd.DataFrame:
        if self.merged_data.empty:
            return pd.DataFrame()
        
        df = self.merged_data.copy()
        #Converts dates to monthly or quarterly periods
        df['period'] = df['load_date'].dt.to_period('M' if period == 'monthly' else 'Q')
        
        # Aggregate by period
        agg_data = df.groupby('period').agg({
            'revenue': 'sum',
            'fuel_surcharge': 'sum',
            'accessorial_charges': 'sum',
            'profit': 'sum',
            'load_id': 'count',
            'actual_distance_miles': 'sum'
        }).reset_index()
        
        #Key derived KPIs
        agg_data.columns = ['period', 'total_revenue', 'total_fuel_cost', 'total_accessorial_cost', 
                           'total_profit', 'total_loads', 'total_miles']
        
        agg_data['total_cost'] = agg_data['total_fuel_cost'] + agg_data['total_accessorial_cost']
        agg_data['profit_margin'] = (agg_data['total_profit'] / agg_data['total_revenue']) * 100
        agg_data['revenue_per_mile'] = agg_data['total_revenue'] / agg_data['total_miles']
        agg_data['cost_per_mile'] = agg_data['total_cost'] / agg_data['total_miles']
        agg_data['profit_per_mile'] = agg_data['total_profit'] / agg_data['total_miles']
        
        # Convert period to string for plotting
        agg_data['period_str'] = agg_data['period'].astype(str)
        
        return agg_data
    
    def profit_margin_by_route(self, top_n: int = 15) -> pd.DataFrame:
        
        if self.merged_data.empty:
            return pd.DataFrame()
        
        df = self.merged_data.copy()
        
        # Group by route (origin-destination pair)
        #Creates readable route name like "Dallas → Chicago"
        df['route'] = df['origin_city'] + ' → ' + df['destination_city']
        
        route_analysis = df.groupby('route').agg({
            'load_id': 'count',
            'revenue': 'sum',
            'profit': 'sum',
            'actual_distance_miles': 'mean',
            'revenue_per_mile': 'mean'
        }).reset_index()
        
        #Ranks routes by profitability %, not just total dollars
        route_analysis.columns = ['route', 'total_loads', 'total_revenue', 'total_profit', 
                                 'avg_distance', 'avg_revenue_per_mile']
        
        route_analysis['profit_margin'] = (route_analysis['total_profit'] / route_analysis['total_revenue']) * 100
        route_analysis['profit_per_mile'] = route_analysis['total_profit'] / (route_analysis['total_loads'] * route_analysis['avg_distance'])
        
        # Sort by profit margin and get top N
        route_analysis = route_analysis.sort_values('profit_margin', ascending=False).head(top_n)
        
        return route_analysis
    
    def cost_per_mile_trends(self, window: int = 30) -> pd.DataFrame:
        
        if self.merged_data.empty:
            return pd.DataFrame()
        
        df = self.merged_data.copy()
        
        # Calculate daily aggregates
        daily_metrics = df.groupby('load_date').agg({
            'revenue': 'sum',
            'fuel_surcharge': 'sum',
            'accessorial_charges': 'sum',
            'actual_distance_miles': 'sum',
            'load_id': 'count'
        }).reset_index()
        
        daily_metrics['daily_cost'] = daily_metrics['fuel_surcharge'] + daily_metrics['accessorial_charges']
        daily_metrics['cost_per_mile'] = daily_metrics['daily_cost'] / daily_metrics['actual_distance_miles']
        daily_metrics['revenue_per_mile'] = daily_metrics['revenue'] / daily_metrics['actual_distance_miles']
        
        # Calculate rolling averages
        daily_metrics['cpm_rolling_avg'] = daily_metrics['cost_per_mile'].rolling(window=window, min_periods=1).mean()
        daily_metrics['rpm_rolling_avg'] = daily_metrics['revenue_per_mile'].rolling(window=window, min_periods=1).mean()
        daily_metrics['profit_margin_rolling'] = ((daily_metrics['revenue_per_mile'] - daily_metrics['cost_per_mile']) / 
                                                  daily_metrics['revenue_per_mile']) * 100
        
        return daily_metrics
    
    def _calculate_kpis(self) -> pd.DataFrame:
        
        if self.merged_data.empty:
            return pd.DataFrame()
        
        df = self.merged_data.copy()
        
        kpis = {
            'Total Revenue ($)': df['revenue'].sum(),
            'Total Profit ($)': df['profit'].sum(),
            'Average Profit Margin (%)': (df['profit'].sum() / df['revenue'].sum()) * 100,
            'Average Revenue per Load ($)': df['revenue'].mean(),
            'Average Cost per Mile ($)': (df['fuel_surcharge'].sum() + df['accessorial_charges'].sum()) / df['actual_distance_miles'].sum(),
            'Average Revenue per Mile ($)': df['revenue'].sum() / df['actual_distance_miles'].sum(),
            'Total Loads': df['load_id'].nunique(),
            'Total Miles': df['actual_distance_miles'].sum(),
            'Top Customer by Revenue': df.groupby('customer_name')['revenue'].sum().idxmax() if not df.empty else 'N/A',
            'Most Profitable Route': df.groupby(['origin_city', 'destination_city'])['profit'].sum().idxmax() if not df.empty else 'N/A'
        }
        
        return pd.DataFrame(list(kpis.items()), columns=['KPI', 'Value'])
    
    def generate_financial_dashboard_data(self) -> Dict[str, pd.DataFrame]:
        dashboard_data = {}
        
        # 1. Revenue vs Cost Analysis
        print("Generating Revenue vs Cost Analysis...")
        dashboard_data['revenue_vs_cost'] = self.revenue_vs_cost_analysis('monthly')
        
        # 2. Profit Margins by Route
        print("Analyzing Profit Margins by Route...")
        dashboard_data['route_profitability'] = self.profit_margin_by_route(top_n=20)
        
        # 3. Cost Per Mile Trends
        print("Calculating Cost Per Mile Trends...")
        dashboard_data['cpm_trends'] = self.cost_per_mile_trends(window=30)
        
        # 4. Key Financial KPIs
        print("Calculating Key Financial KPIs...")
        dashboard_data['kpis'] = self._calculate_kpis()
        
        print("✅ Financial dashboard data generated successfully!")
        return dashboard_data
    
   
    
    def export_financial_report(self, dashboard_data: Dict[str, pd.DataFrame], 
                               output_path: str = "reports/"):
        
        import os
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_path}/financial_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Write each dataframe to a separate sheet
            for sheet_name, df in dashboard_data.items():
                # Truncate sheet name if too long
                safe_sheet_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            # Add summary sheet
            summary_df = self._create_summary_sheet(dashboard_data)
            summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
            
            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✅ Financial report exported to {filename}")
        return filename
    
    def _create_summary_sheet(self, dashboard_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create executive summary sheet for Excel report"""
        summary_data = []
        
        # Overall metrics
        kpis = dashboard_data['kpis']
        for _, row in kpis.iterrows():
            summary_data.append({
                'Category': 'Overall',
                'Metric': row['KPI'],
                'Value': row['Value']
            })
        
        # Top 3 routes
        routes = dashboard_data['route_profitability'].head(3)
        for _, row in routes.iterrows():
            summary_data.append({
                'Category': 'Top Routes',
                'Metric': f"{row['route']}",
                'Value': f"{row['profit_margin']:.1f}% margin"
            })
        
        # Top 3 customers
        customers = dashboard_data['customer_profitability'].head(3)
        for _, row in customers.iterrows():
            summary_data.append({
                'Category': 'Top Customers',
                'Metric': row['customer_name'],
                'Value': f"${row['total_revenue']/1e6:.2f}M revenue"
            })
        
        return pd.DataFrame(summary_data)


# === MAIN EXECUTION ===
if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("FLEETSMART FINANCIAL ANALYZER")
    print("=" * 60)
    
    try:
        # Load and preprocess data
        engine = DataEngine()
        prep = DataPreprocessor(engine)
        processed_data = prep.run_pipeline()
        
        # Initialize financial analyzer
        analyzer = FinancialAnalyzer(processed_data)
        
        # Generate dashboard data
        print("\n" + "=" * 60)
        print("GENERATING FINANCIAL DASHBOARD DATA")
        print("=" * 60)
        
        dashboard_data = analyzer.generate_financial_dashboard_data()
        
        # Create visualizations
        print("\n" + "=" * 60)
        print("CREATING VISUALIZATIONS")
        print("=" * 60)
        analyzer.create_visualizations(dashboard_data, save_path="visualizations")
        
        # Export report
        print("\n" + "=" * 60)
        print("EXPORTING FINANCIAL REPORT")
        print("=" * 60)
        report_path = analyzer.export_financial_report(dashboard_data, output_path="reports")
        
        # Print summary
        print("\n" + "=" * 60)
        print("FINANCIAL ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"📊 Total Records Analyzed: {analyzer.merged_data.shape[0]:,}")
        print(f"💰 Total Revenue: ${analyzer.merged_data['revenue'].sum()/1e6:.2f}M")
        print(f"📈 Average Profit Margin: {(analyzer.merged_data['profit'].sum()/analyzer.merged_data['revenue'].sum())*100:.1f}%")
        print(f"📁 Report saved to: {report_path}")
        
    except Exception as e:
        print(f"❌ Error in financial analysis: {e}")
        import traceback
        traceback.print_exc()