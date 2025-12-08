import pandas as pd
import numpy as np
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

class DriverAnalyzer:
    def __init__(self, processed_data: Dict[str, pd.DataFrame]):
        
        self.data = processed_data  # Stores the cleaned datasets
        
        # Initialize main driver dataset
        self.driver_data = None
        self._prepare_driver_data()
    
    def _prepare_driver_data(self):
        try:
            # 1. Start with driver monthly metrics if available
            if 'driver_monthly_metrics' in self.data and not self.data['driver_monthly_metrics'].empty:
                driver_data = self.data['driver_monthly_metrics'].copy()
                # Ensure month is datetime
                if 'month' in driver_data.columns:
                    driver_data['month'] = pd.to_datetime(driver_data['month'], errors='coerce')
            else:
                # Calculate from trips and loads if monthly metrics not available
                driver_data = self._calculate_driver_metrics_from_trips()
            
            # 2. Merge with driver info
            if 'drivers' in self.data and not self.data['drivers'].empty:
                driver_info = self.data['drivers'][[
                    'driver_id', 'first_name', 'last_name', 'hire_date', 
                    'employment_status', 'home_terminal', 'cdl_class'
                ]].copy()
                
                driver_data = pd.merge(
                    driver_data,
                    driver_info,
                    left_on='driver_id',
                    right_on='driver_id',
                    how='left'
                )
                
                # Create full name
                driver_data['full_name'] = driver_data['first_name'] + ' ' + driver_data['last_name']
            
            # 3. Calculate derived metrics
            driver_data = self._calculate_derived_metrics(driver_data)
            
            self.driver_data = driver_data
            print(f"Driver dataset prepared: {self.driver_data.shape[0]:,} records")
            
        except Exception as e:
            print(f"Error preparing driver data: {e}")
            self.driver_data = pd.DataFrame()
    
    def _calculate_driver_metrics_from_trips(self):
        try:
            # Merge trips with loads
            trips_data = pd.merge(
                self.data['trips'],
                self.data['loads'][['load_id', 'revenue']],
                left_on='load_id',
                right_on='load_id',
                how='inner'
            )
            
            # Extract month from dispatch date
            trips_data['dispatch_date'] = pd.to_datetime(trips_data['dispatch_date'])
            trips_data['month'] = trips_data['dispatch_date'].dt.to_period('M')
            
            # Group by driver and month
            driver_metrics = trips_data.groupby(['driver_id', 'month']).agg({
                'load_id': 'count',
                'actual_distance_miles': 'sum',
                'revenue': 'sum',
                'fuel_gallons_used': 'sum',
                'idle_time_hours': 'sum'
            }).reset_index()
            
            driver_metrics.columns = [
                'driver_id', 'month', 'trips_completed', 'total_miles',
                'total_revenue', 'total_fuel_gallons', 'idle_time_hours'
            ]
            
            # Calculate MPG
            driver_metrics['average_mpg'] = np.where(
                driver_metrics['total_fuel_gallons'] > 0,
                driver_metrics['total_miles'] / driver_metrics['total_fuel_gallons'],
                0
            )
            
            # Convert month to datetime
            driver_metrics['month'] = driver_metrics['month'].dt.to_timestamp()
            
            return driver_metrics
            
        except Exception as e:
            print(f"Error calculating driver metrics: {e}")
            return pd.DataFrame()
    
    def _calculate_derived_metrics(self, df):
        df = df.copy()
        
        # Calculate scores (0-100 scale)
        
        # 1. Efficiency Score (based on MPG)
        if 'average_mpg' in df.columns:
            # Normalize MPG: 6 MPG = 70, 8 MPG = 90, 10 MPG = 100
            df['efficiency_score'] = np.clip((df['average_mpg'] - 6) * 10 + 70, 40, 100)
        else:
            df['efficiency_score'] = 70
        
        # 2. Productivity Score (based on trips and miles)
        if 'trips_completed' in df.columns and 'total_miles' in df.columns:
            trips_norm = (df['trips_completed'] - df['trips_completed'].mean()) / df['trips_completed'].std() if df['trips_completed'].std() > 0 else 0
            miles_norm = (df['total_miles'] - df['total_miles'].mean()) / df['total_miles'].std() if df['total_miles'].std() > 0 else 0
            df['productivity_score'] = np.clip((trips_norm * 0.4 + miles_norm * 0.6) * 15 + 70, 0, 100)
        else:
            df['productivity_score'] = 70
        
        # 3. Revenue Score
        if 'total_revenue' in df.columns:
            revenue_norm = (df['total_revenue'] - df['total_revenue'].mean()) / df['total_revenue'].std() if df['total_revenue'].std() > 0 else 0
            df['revenue_score'] = np.clip(revenue_norm * 15 + 70, 0, 100)
        else:
            df['revenue_score'] = 70
        
        # 4. Overall Score (weighted average)
        df['overall_score'] = (
            df['efficiency_score'] * 0.25 +
            df['productivity_score'] * 0.35 +
            df['revenue_score'] * 0.40
        )
        
        # 5. Performance Tier
        df['performance_tier'] = pd.cut(
            df['overall_score'],
            bins=[0, 60, 70, 80, 90, 100],
            labels=['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'],
            include_lowest=True
        )
        
        return df
    
    def get_driver_scorecards(self, top_n: int = 20):
        if self.driver_data.empty:
            return pd.DataFrame(), {}
        
        # Get latest month for each driver
        latest_data = self.driver_data.sort_values(['driver_id', 'month']).groupby('driver_id').last().reset_index()
        
        # Add ranking
        latest_data['rank'] = latest_data['overall_score'].rank(method='dense', ascending=True).astype(int)
        latest_data = latest_data.sort_values('rank')
        
        # Select top N
        scorecards = latest_data.head(top_n).copy()
        
        # Generate summary
        summary = {
            'total_drivers': len(latest_data),
            'avg_overall_score': latest_data['overall_score'].mean(),
            'avg_efficiency_score': latest_data['efficiency_score'].mean(),
            'avg_productivity_score': latest_data['productivity_score'].mean(),
            'top_3_drivers': scorecards.head(3)[['full_name', 'overall_score', 'performance_tier']].to_dict('records'),
            'performance_distribution': latest_data['performance_tier'].value_counts().to_dict()
        }
        
        return scorecards, summary
    
    def get_safety_analysis(self):
        #Analyze safety incidents
        if 'safety_incidents' not in self.data or self.data['safety_incidents'].empty:
            return pd.DataFrame(), {}
        
        incidents = self.data['safety_incidents'].copy()
        
        # Ensure date is datetime
        if 'incident_date' in incidents.columns:
            incidents['incident_date'] = pd.to_datetime(incidents['incident_date'], errors='coerce')
            incidents['month'] = incidents['incident_date'].dt.to_period('M')
        
        # Monthly trend
        monthly_trend = incidents.groupby('month').agg({
            'incident_id': 'count',
            'preventable_flag': 'sum',
            'at_fault_flag': 'sum',
            'vehicle_damage_cost': 'sum',
            'cargo_damage_cost': 'sum'
        }).reset_index()
        
        monthly_trend.columns = ['month', 'incident_count', 'preventable_count', 'at_fault_count', 
                                 'vehicle_damage', 'cargo_damage']
        monthly_trend['total_damage'] = monthly_trend['vehicle_damage'] + monthly_trend['cargo_damage']
        monthly_trend['month'] = monthly_trend['month'].dt.to_timestamp()
        
        # Driver incident analysis
        driver_incidents = incidents.groupby('driver_id').agg({
            'incident_id': 'count',
            'preventable_flag': 'sum',
            'at_fault_flag': 'sum'
        }).reset_index()
        
        driver_incidents.columns = ['driver_id', 'incident_count', 'preventable_count', 'at_fault_count']
        
        # Merge with driver names
        if 'drivers' in self.data:
            driver_names = self.data['drivers'][['driver_id', 'first_name', 'last_name']]
            driver_incidents = pd.merge(driver_incidents, driver_names, on='driver_id', how='left')
            driver_incidents['driver_name'] = driver_incidents['first_name'] + ' ' + driver_incidents['last_name']
        else:
            driver_incidents['driver_name'] = 'Driver ' + driver_incidents['driver_id'].astype(str)
        
        # Summary statistics
        summary = {
            'total_incidents': len(incidents),
            'preventable_incidents': incidents['preventable_flag'].sum() if 'preventable_flag' in incidents.columns else 0,
            'at_fault_incidents': incidents['at_fault_flag'].sum() if 'at_fault_flag' in incidents.columns else 0,
            'total_damage_cost': (incidents['vehicle_damage_cost'].sum() if 'vehicle_damage_cost' in incidents.columns else 0) +
                                (incidents['cargo_damage_cost'].sum() if 'cargo_damage_cost' in incidents.columns else 0),
            'worst_drivers': driver_incidents.sort_values('incident_count', ascending=False).head(5).to_dict('records')
        }
        
        return monthly_trend, summary
    
    def get_retention_risk_assessment(self):
        """Assess retention risk for drivers"""
        if self.driver_data.empty:
            return pd.DataFrame(), {}
        
        # Get latest data for each driver
        latest_data = self.driver_data.sort_values(['driver_id', 'month']).groupby('driver_id').last().reset_index()
        
        # Calculate risk factors
        risk_factors = []
        
        # Factor 1: Low overall score
        if 'overall_score' in latest_data.columns:
            latest_data['score_risk'] = pd.cut(latest_data['overall_score'],
                                             bins=[0, 60, 75, 100],
                                             labels=['High', 'Medium', 'Low'])
            risk_factors.append(latest_data['score_risk'])
        
        # Factor 2: Low productivity
        if 'trips_completed' in latest_data.columns:
            p25 = latest_data['trips_completed'].quantile(0.25)
            latest_data['productivity_risk'] = np.where(
                latest_data['trips_completed'] < p25, 'High', 'Medium'
            )
            risk_factors.append(latest_data['productivity_risk'])
        
        # Combine risk factors
        if risk_factors:
            # Simple logic: if any factor is High, overall risk is High
            latest_data['retention_risk'] = 'Medium'  # Default
            
            for i in range(len(latest_data)):
                risks = []
                for factor in risk_factors:
                    if i < len(factor):
                        risks.append(factor.iloc[i])
                
                if 'High' in risks:
                    latest_data.at[i, 'retention_risk'] = 'High'
                elif all(r == 'Low' for r in risks):
                    latest_data.at[i, 'retention_risk'] = 'Low'
        else:
            latest_data['retention_risk'] = 'Medium'
        
        # Prepare risk assessment
        risk_assessment = latest_data[['driver_id', 'full_name', 'overall_score', 
                                      'performance_tier', 'retention_risk', 
                                      'trips_completed', 'total_miles']].copy()
        
        risk_assessment = risk_assessment.sort_values('retention_risk', ascending=False)
        
        # Summary
        risk_summary = {
            'total_drivers': len(risk_assessment),
            'high_risk_count': (risk_assessment['retention_risk'] == 'High').sum(),
            'medium_risk_count': (risk_assessment['retention_risk'] == 'Medium').sum(),
            'low_risk_count': (risk_assessment['retention_risk'] == 'Low').sum(),
            'high_risk_percentage': ((risk_assessment['retention_risk'] == 'High').sum() / len(risk_assessment)) * 100,
            'top_concerns': risk_assessment[risk_assessment['retention_risk'] == 'High'].head(5).to_dict('records')
        }
        
        return risk_assessment, risk_summary
    
    def generate_dashboard_summary(self):
        """Generate formatted summary of driver performance"""
        output = []
        
        # Get all analyses
        scorecards, score_summary = self.get_driver_scorecards()
        safety_trend, safety_summary = self.get_safety_analysis()
        risk_assessment, risk_summary = self.get_retention_risk_assessment()
        
        # 1. DRIVER SCORECARDS
        output.append("=" * 60)
        output.append("DRIVER SCORECARDS & RANKINGS")
        output.append("=" * 60)
        
        if score_summary:
            output.append(f"Total Drivers Analyzed: {score_summary.get('total_drivers', 0)}")
            output.append(f"Average Overall Score: {score_summary.get('avg_overall_score', 0):.1f}/100")
            output.append("")
            output.append("🏆 TOP 3 DRIVERS:")
            
            for i, driver in enumerate(score_summary.get('top_3_drivers', []), 1):
                name = driver.get('full_name', f'Driver {i}')
                score = driver.get('overall_score', 0)
                tier = driver.get('performance_tier', 'N/A')
                output.append(f"  {i}. {name}: {score:.1f}/100 ({tier})")
            
            output.append("")
            output.append("Performance Distribution:")
            dist = score_summary.get('performance_distribution', {})
            for tier in ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']:
                if tier in dist:
                    count = dist[tier]
                    percentage = (count / score_summary['total_drivers']) * 100 if score_summary['total_drivers'] > 0 else 0
                    output.append(f"  {tier}: {count} drivers ({percentage:.1f}%)")
        
        output.append("")
        
        # 2. SAFETY INCIDENT ANALYSIS
        output.append("=" * 60)
        output.append("SAFETY INCIDENT ANALYSIS")
        output.append("=" * 60)
        
        if safety_summary:
            output.append(f"Total Incidents: {safety_summary.get('total_incidents', 0):,}")
            output.append(f"Preventable Incidents: {safety_summary.get('preventable_incidents', 0):,}")
            output.append(f"At-Fault Incidents: {safety_summary.get('at_fault_incidents', 0):,}")
            output.append(f"Total Damage Cost: ${safety_summary.get('total_damage_cost', 0):,.2f}")
            
            if 'worst_drivers' in safety_summary and safety_summary['worst_drivers']:
                output.append("")
                output.append("🚨 DRIVERS WITH MOST INCIDENTS:")
                for i, driver in enumerate(safety_summary['worst_drivers'][:3], 1):
                    name = driver.get('driver_name', f'Driver {driver.get("driver_id", i)}')
                    incidents = driver.get('incident_count', 0)
                    output.append(f"  {i}. {name}: {incidents} incidents")
        
        output.append("")
        
        # 3. RETENTION RISK ASSESSMENT
        output.append("=" * 60)
        output.append("RETENTION RISK ASSESSMENT")
        output.append("=" * 60)
        
        if risk_summary:
            output.append(f"Total Drivers: {risk_summary.get('total_drivers', 0):,}")
            output.append(f"High Risk: {risk_summary.get('high_risk_count', 0)} drivers ({risk_summary.get('high_risk_percentage', 0):.1f}%)")
            output.append(f"Medium Risk: {risk_summary.get('medium_risk_count', 0)} drivers")
            output.append(f"Low Risk: {risk_summary.get('low_risk_count', 0)} drivers")
            
            if 'top_concerns' in risk_summary and risk_summary['top_concerns']:
                output.append("")
                output.append("⚠️ TOP RETENTION CONCERNS:")
                for i, driver in enumerate(risk_summary['top_concerns'][:3], 1):
                    name = driver.get('full_name', f'Driver {driver.get("driver_id", i)}')
                    score = driver.get('overall_score', 0)
                    trips = driver.get('trips_completed', 0)
                    output.append(f"  {i}. {name}: Score {score:.1f}, {trips} trips")
        
        return "\n".join(output)
    
    def generate_driver_dashboard_data(self):
        """Generate all data for dashboard"""
        dashboard_data = {}
        
        print("Generating Driver Scorecards...")
        scorecards, score_summary = self.get_driver_scorecards()
        dashboard_data['driver_scorecards'] = scorecards
        dashboard_data['score_summary'] = pd.DataFrame([score_summary])
        
        print("Analyzing Safety Incidents...")
        safety_trend, safety_summary = self.get_safety_analysis()
        dashboard_data['safety_trends'] = safety_trend
        dashboard_data['safety_summary'] = pd.DataFrame([safety_summary])
        
        print("Assessing Retention Risk...")
        risk_assessment, risk_summary = self.get_retention_risk_assessment()
        dashboard_data['retention_risk'] = risk_assessment
        dashboard_data['risk_summary'] = pd.DataFrame([risk_summary])
        
        print("Driver dashboard data generated successfully!")
        return dashboard_data


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 60)
    print("FLEETSMART DRIVER PERFORMANCE ANALYZER")
    print("=" * 60)
    
    try:
        # Load and preprocess data
        engine = DataEngine()
        prep = DataPreprocessor(engine)
        processed_data = prep.run_pipeline()
        
        # Initialize driver analyzer
        analyzer = DriverAnalyzer(processed_data)
        
        # Generate and print formatted summary
        print("\n" + "=" * 60)
        print("GENERATING DRIVER DASHBOARD SUMMARY")
        print("=" * 60 + "\n")
        
        summary = analyzer.generate_dashboard_summary()
        print(summary)
        
        # Also generate full dashboard data
        print("\n" + "=" * 60)
        print("GENERATING FULL DASHBOARD DATA")
        print("=" * 60)
        dashboard_data = analyzer.generate_driver_dashboard_data()
        
        # Print additional metrics
        print("\n" + "=" * 60)
        print("DRIVER ANALYSIS COMPLETE")
        print("=" * 60)
        if not analyzer.driver_data.empty:
            total_drivers = analyzer.driver_data['driver_id'].nunique()
            avg_score = analyzer.driver_data['overall_score'].mean() if 'overall_score' in analyzer.driver_data.columns else 0
            
            print(f"Total Drivers Analyzed: {total_drivers:,}")
            print(f"Average Overall Score: {avg_score:.1f}/100")
            print(f"Driver Records: {analyzer.driver_data.shape[0]:,}")
        
    except Exception as e:
        print(f"Error in driver analysis: {e}")
        import traceback
        traceback.print_exc()