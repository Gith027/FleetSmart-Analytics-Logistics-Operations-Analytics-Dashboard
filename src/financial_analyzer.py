import pandas as pd
import numpy as np
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from typing import Dict
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

class FinancialAnalyzer:
    def __init__(self, processed_data: Dict[str, pd.DataFrame]):
        
        self.data = processed_data  # Stores the cleaned datasets
        
        # Sets analysis period: 3 full years (2022–2024)
        self.start_date = pd.Timestamp('2022-01-01')
        self.end_date = pd.Timestamp('2024-12-31')
        
        # Initialize main merged dataset
        self.merged_data = None
        self._prepare_merged_data()
        
        # For enhanced cost breakdown
        self.cost_breakdown_data = None
        self._prepare_cost_breakdown()
    
    def _prepare_merged_data(self):
        try:
            # 1. Merge loads with trips
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
    
    def _prepare_cost_breakdown(self):
        try:
            # Merge with fuel purchases and maintenance for cost breakdown
            if 'fuel_purchases' in self.data and 'maintenance_records' in self.data:
                # Get fuel cost per truck per month
                fuel_costs = self.data['fuel_purchases'].copy()
                fuel_costs['purchase_date'] = pd.to_datetime(fuel_costs['purchase_date'])
                fuel_costs = fuel_costs[
                    (fuel_costs['purchase_date'] >= self.start_date) & 
                    (fuel_costs['purchase_date'] <= self.end_date)
                ]
                
                # Get maintenance cost per truck per month
                maintenance_costs = self.data['maintenance_records'].copy()
                maintenance_costs['maintenance_date'] = pd.to_datetime(maintenance_costs['maintenance_date'])
                maintenance_costs = maintenance_costs[
                    (maintenance_costs['maintenance_date'] >= self.start_date) & 
                    (maintenance_costs['maintenance_date'] <= self.end_date)
                ]
                
                self.cost_breakdown_data = {
                    'fuel': fuel_costs,
                    'maintenance': maintenance_costs
                }
        except Exception as e:
            print(f"Could not prepare cost breakdown data: {e}")
            self.cost_breakdown_data = None
    
    def revenue_vs_cost_analysis(self, period: str = 'monthly') -> pd.DataFrame:
       
        if self.merged_data.empty:
            return pd.DataFrame(), {}
        
        df = self.merged_data.copy()
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
        
        agg_data.columns = ['period', 'total_revenue', 'total_fuel_cost', 'total_accessorial_cost', 
                           'total_profit', 'total_loads', 'total_miles']
        
        agg_data['total_cost'] = agg_data['total_fuel_cost'] + agg_data['total_accessorial_cost']
        agg_data['profit_margin'] = (agg_data['total_profit'] / agg_data['total_revenue']) * 100
        agg_data['revenue_per_mile'] = agg_data['total_revenue'] / agg_data['total_miles']
        agg_data['cost_per_mile'] = agg_data['total_cost'] / agg_data['total_miles']
        agg_data['profit_per_mile'] = agg_data['total_profit'] / agg_data['total_miles']
        agg_data['period_str'] = agg_data['period'].astype(str)
        
        # Calculate summary statistics
        summary = {
            'total_revenue': agg_data['total_revenue'].sum(),
            'total_profit': agg_data['total_profit'].sum(),
            'avg_profit_margin': agg_data['profit_margin'].mean(),
            'best_month': agg_data.loc[agg_data['profit_margin'].idxmax()],
            'worst_month': agg_data.loc[agg_data['profit_margin'].idxmin()],
            'analysis_period': f"{agg_data['period_str'].iloc[0][:7]} to {agg_data['period_str'].iloc[-1][:7]}"
        }
        
        return agg_data, summary
    
    def profit_margin_by_route(self, min_trips: int = 5) -> pd.DataFrame:
        
        if self.merged_data.empty:
            return pd.DataFrame(), {}
        
        df = self.merged_data.copy()
        df['route'] = df['origin_city'] + ' ->  ' + df['destination_city']
        
        # Group by route with trip count filter
        route_stats = df.groupby('route').agg({
            'load_id': 'count',
            'revenue': 'sum',
            'profit': 'sum',
            'actual_distance_miles': ['sum', 'mean'],
            'fuel_surcharge': 'sum',
            'accessorial_charges': 'sum'
        }).reset_index()
        
        # Flatten column names
        route_stats.columns = ['route', 'trip_count', 'total_revenue', 'total_profit', 
                              'total_miles', 'avg_distance', 'fuel_cost', 'accessorial_cost']
        
        # Apply minimum trips filter
        route_stats = route_stats[route_stats['trip_count'] >= min_trips].copy()
        
        # Calculate metrics
        route_stats['profit_margin'] = (route_stats['total_profit'] / route_stats['total_revenue']) * 100
        route_stats['profit_per_mile'] = route_stats['total_profit'] / route_stats['total_miles']
        route_stats['revenue_per_mile'] = route_stats['total_revenue'] / route_stats['total_miles']
        route_stats['cost_per_mile'] = (route_stats['fuel_cost'] + route_stats['accessorial_cost']) / route_stats['total_miles']
        
        # Calculate route profitability categories
        def categorize_profitability(margin):
            if margin > 30:
                return 'Excellent'
            elif margin > 20:
                return 'Good'
            elif margin > 10:
                return 'Fair'
            elif margin > 0:
                return 'Marginal'
            else:
                return 'Loss'
        
        route_stats['profit_category'] = route_stats['profit_margin'].apply(categorize_profitability)
        
        # Sort by profit margin
        route_stats = route_stats.sort_values('profit_margin', ascending=False).reset_index(drop=True)
        
        # Generate summary
        category_counts = route_stats['profit_category'].value_counts().to_dict()
        summary = {
            'total_routes': len(route_stats),
            'top_3': route_stats.head(3)[['route', 'profit_margin', 'total_profit']].to_dict('records'),
            'bottom_3': route_stats.tail(3)[['route', 'profit_margin', 'total_profit']].to_dict('records'),
            'category_distribution': category_counts,
            'category_percentages': {k: (v/len(route_stats)*100) for k, v in category_counts.items()}
        }
        
        return route_stats, summary
    
    def cost_per_mile_trends(self, window: int = 30) -> pd.DataFrame:
        
        if self.merged_data.empty:
            return pd.DataFrame(), {}
        
        df = self.merged_data.copy()
        
        # Daily aggregates
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
        daily_metrics['profit_per_mile'] = daily_metrics['revenue_per_mile'] - daily_metrics['cost_per_mile']
        
        # Rolling averages
        daily_metrics['cpm_rolling_avg'] = daily_metrics['cost_per_mile'].rolling(window=window, min_periods=1).mean()
        daily_metrics['rpm_rolling_avg'] = daily_metrics['revenue_per_mile'].rolling(window=window, min_periods=1).mean()
        
        # Calculate fuel and maintenance CPM if breakdown data is available
        fuel_cpm, maintenance_cpm = None, None
        fuel_percentage, maintenance_percentage = None, None
        
        if self.cost_breakdown_data:
            # Calculate fuel CPM from fuel purchases
            if not self.cost_breakdown_data['fuel'].empty:
                total_fuel_cost = self.cost_breakdown_data['fuel']['total_cost'].sum()
                total_miles = df['actual_distance_miles'].sum()
                fuel_cpm = total_fuel_cost / total_miles
            
            # Calculate maintenance CPM from maintenance records
            if not self.cost_breakdown_data['maintenance'].empty:
                total_maintenance_cost = self.cost_breakdown_data['maintenance']['total_cost'].sum()
                total_miles = df['actual_distance_miles'].sum()
                maintenance_cpm = total_maintenance_cost / total_miles
        
        # Use approximate breakdown if detailed data not available
        if fuel_cpm is None or maintenance_cpm is None:
            # Estimate based on industry averages and available data
            avg_cpm = daily_metrics['cost_per_mile'].mean()
            fuel_cpm = avg_cpm * 0.638  # Industry average ~63.8%
            maintenance_cpm = avg_cpm * 0.275  # Industry average ~27.5%
        
        # Calculate percentages
        avg_cpm = daily_metrics['cost_per_mile'].mean()
        fuel_percentage = (fuel_cpm / avg_cpm) * 100
        maintenance_percentage = (maintenance_cpm / avg_cpm) * 100
        
        # Calculate trend
        first_quarter = daily_metrics.iloc[:90]['cost_per_mile'].mean()  # First 90 days
        last_quarter = daily_metrics.iloc[-90:]['cost_per_mile'].mean()   # Last 90 days
        trend_percentage = ((last_quarter - first_quarter) / first_quarter) * 100
        trend_direction = "DECREASING" if trend_percentage < 0 else "INCREASING"
        
        summary = {
            'avg_cpm': avg_cpm,
            'high_cpm': daily_metrics['cost_per_mile'].max(),
            'low_cpm': daily_metrics['cost_per_mile'].min(),
            'high_cpm_date': daily_metrics.loc[daily_metrics['cost_per_mile'].idxmax(), 'load_date'],
            'low_cpm_date': daily_metrics.loc[daily_metrics['cost_per_mile'].idxmin(), 'load_date'],
            'trend_percentage': abs(trend_percentage),
            'trend_direction': trend_direction,
            'fuel_cpm': fuel_cpm,
            'maintenance_cpm': maintenance_cpm,
            'fuel_percentage': fuel_percentage,
            'maintenance_percentage': maintenance_percentage,
            'analysis_period': f"{daily_metrics['load_date'].min():%Y-%m} to {daily_metrics['load_date'].max():%Y-%m}"
        }
        
        return daily_metrics, summary
    
    def _calculate_kpis(self) -> pd.DataFrame:
        """Calculate key financial KPIs with formatting"""
        if self.merged_data.empty:
            return pd.DataFrame()
        
        df = self.merged_data.copy()
        
        kpis = {
            'Total Revenue': df['revenue'].sum(),
            'Total Profit': df['profit'].sum(),
            'Average Profit Margin': (df['profit'].sum() / df['revenue'].sum()) * 100,
            'Average Revenue per Load': df['revenue'].mean(),
            'Average Cost per Mile': (df['fuel_surcharge'].sum() + df['accessorial_charges'].sum()) / df['actual_distance_miles'].sum(),
            'Average Revenue per Mile': df['revenue'].sum() / df['actual_distance_miles'].sum(),
            'Total Loads': df['load_id'].nunique(),
            'Total Miles': df['actual_distance_miles'].sum()
        }
        
        return pd.DataFrame(list(kpis.items()), columns=['KPI', 'Value'])
    
    def generate_dashboard_summary(self) -> str:
        output = []
        
        # Get all analyses
        rev_cost_data, rev_cost_summary = self.revenue_vs_cost_analysis()
        route_stats, route_summary = self.profit_margin_by_route()
        cpm_trends, cpm_summary = self.cost_per_mile_trends()
        
        # 1. REVENUE VS COST ANALYSIS
        output.append("=" * 60)
        output.append("REVENUE VS COST ANALYSIS")
        output.append("=" * 60)
        output.append(f"Analysis Period: {rev_cost_summary.get('analysis_period', 'N/A')}")
        output.append(f"Total Revenue: ${rev_cost_summary.get('total_revenue', 0):,.2f}")
        output.append(f"Total Profit: ${rev_cost_summary.get('total_profit', 0):,.2f}")
        output.append(f"Average Profit Margin: {rev_cost_summary.get('avg_profit_margin', 0):.2f}%")
        
        if 'best_month' in rev_cost_summary:
            best = rev_cost_summary['best_month']
            worst = rev_cost_summary['worst_month']
            output.append(f"Best Month: {best['period_str'][:7]} ({best['profit_margin']:.1f}% margin)")
            output.append(f"Worst Month: {worst['period_str'][:7]} ({worst['profit_margin']:.1f}% margin)")
        
        output.append("")  # Empty line for spacing
        
        # 2. PROFIT MARGINS BY ROUTE
        output.append("=" * 60)
        output.append("PROFIT MARGINS BY ROUTE")
        output.append("=" * 60)
        
        if route_summary:
            output.append(f"Analyzing {route_summary['total_routes']} routes (min 5 trips each)")
            output.append("Top 3 Most Profitable Routes:")
            
            for i, route in enumerate(route_summary['top_3'][:3], 1):
                margin = route.get('profit_margin', 0)
                profit = route.get('total_profit', 0)
                route_name = route.get('route', 'Unknown')
                output.append(f"  {i}. {route_name}: {margin:.1f}% margin (${profit:,.0f} profit)")
            
            output.append("")
            output.append("Bottom 3 Least Profitable Routes:")
            
            # Reverse bottom routes for proper order
            bottom_routes = route_summary['bottom_3'][::-1]
            for i, route in enumerate(bottom_routes, 1):
                margin = route.get('profit_margin', 0)
                route_name = route.get('route', 'Unknown')
                loss_text = "LOSS" if margin < 0 else ""
                margin_text = f"{margin:.1f}% margin" if margin >= 0 else f"{abs(margin):.1f}%"
                output.append(f"  {route_summary['total_routes'] - i + 1}. {route_name}: {loss_text} {margin_text}")
            
            output.append("")
            output.append("Profitability Distribution:")
            
            # Get categories in desired order
            categories_order = ['Excellent', 'Good', 'Fair', 'Marginal', 'Loss']
            for cat in categories_order:
                if cat in route_summary['category_percentages']:
                    count = route_summary['category_distribution'].get(cat, 0)
                    percent = route_summary['category_percentages'].get(cat, 0)
                    output.append(f"  {cat}: {count} routes ({percent:.1f}%)")
        
        output.append("")  # Empty line for spacing
        
        # 3. COST PER MILE TREND ANALYSIS
        output.append("=" * 60)
        output.append("COST PER MILE TREND ANALYSIS")
        output.append("=" * 60)
        
        if cpm_summary:
            output.append(f"Analysis Period: {cpm_summary.get('analysis_period', 'N/A')}")
            output.append(f"Average CPM: ${cpm_summary.get('avg_cpm', 0):.3f}")
            
            if 'high_cpm' in cpm_summary and 'high_cpm_date' in cpm_summary:
                output.append(f"Highest CPM: ${cpm_summary['high_cpm']:.3f} ({cpm_summary['high_cpm_date']:%Y-%m})")
            
            if 'low_cpm' in cpm_summary and 'low_cpm_date' in cpm_summary:
                output.append(f"Lowest CPM: ${cpm_summary['low_cpm']:.3f} ({cpm_summary['low_cpm_date']:%Y-%m})")
            
            output.append(f"Trend: {cpm_summary.get('trend_direction', 'N/A')} ({cpm_summary.get('trend_percentage', 0):.1f}% change)")
            output.append("")
            output.append("Cost Breakdown:")
            
            if 'fuel_cpm' in cpm_summary and 'fuel_percentage' in cpm_summary:
                output.append(f"  Fuel CPM: ${cpm_summary['fuel_cpm']:.3f} ({cpm_summary['fuel_percentage']:.1f}%)")
            
            if 'maintenance_cpm' in cpm_summary and 'maintenance_percentage' in cpm_summary:
                output.append(f"  Maintenance CPM: ${cpm_summary['maintenance_cpm']:.3f} ({cpm_summary['maintenance_percentage']:.1f}%)")
        
        # Join all lines with newline
        return "\n".join(output)
    
    def generate_financial_dashboard_data(self) -> Dict[str, pd.DataFrame]:
        """Generate all data for dashboard with summaries"""
        dashboard_data = {}
        
        print("Generating Revenue vs Cost Analysis...")
        rev_cost_data, rev_cost_summary = self.revenue_vs_cost_analysis('monthly')
        dashboard_data['revenue_vs_cost'] = rev_cost_data
        dashboard_data['revenue_vs_cost_summary'] = pd.DataFrame([rev_cost_summary])
        
        print("Analyzing Profit Margins by Route...")
        route_stats, route_summary = self.profit_margin_by_route()
        dashboard_data['route_profitability'] = route_stats
        dashboard_data['route_summary'] = pd.DataFrame([route_summary])
        
        print("Calculating Cost Per Mile Trends...")
        cpm_trends, cpm_summary = self.cost_per_mile_trends(window=30)
        dashboard_data['cpm_trends'] = cpm_trends
        dashboard_data['cpm_summary'] = pd.DataFrame([cpm_summary])
        
        print("Calculating Key Financial KPIs...")
        dashboard_data['kpis'] = self._calculate_kpis()
        
        print("Financial dashboard data generated successfully!")
        return dashboard_data


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
        
        # Generate and print formatted summary
        print("\n" + "=" * 60)
        print("GENERATING FINANCIAL DASHBOARD SUMMARY")
        print("=" * 60 + "\n")
        
        summary = analyzer.generate_dashboard_summary()
        print(summary)
        
        # Also generate full dashboard data
        print("\n" + "=" * 60)
        print("GENERATING FULL DASHBOARD DATA")
        print("=" * 60)
        dashboard_data = analyzer.generate_financial_dashboard_data()
        print(dashboard_data)
        
        # Print additional metrics
        print("\n" + "=" * 60)
        print("FINANCIAL ANALYSIS COMPLETE")
        print("=" * 60)
        if not analyzer.merged_data.empty:
            total_rev = analyzer.merged_data['revenue'].sum()
            total_profit = analyzer.merged_data['profit'].sum()
            total_margin = (total_profit / total_rev * 100) if total_rev > 0 else 0
            
            print(f"Total Records Analyzed: {analyzer.merged_data.shape[0]:,}")
            print(f"Total Revenue: ${total_rev:,.2f}")
            print(f"verage Profit Margin: {total_margin:.2f}%")
        
    except Exception as e:
        print(f"Error in financial analysis: {e}")
        import traceback
        traceback.print_exc()