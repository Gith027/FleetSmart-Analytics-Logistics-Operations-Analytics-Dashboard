# alerts_engine.py - Centralized Alert Management for FleetSmart Analytics
import pandas as pd
from datetime import datetime

class AlertsEngine:
    """
    Centralized alerts management system that collects and manages alerts
    from all analyzer modules.
    """
    
    def __init__(self, data):
        self.data = data
        self.thresholds = {
            'on_time_rate_critical': 85,
            'on_time_rate_warning': 90,
            'idle_hours_warning': 5,
            'fleet_mpg_warning': 6.0,
            'downtime_hours_critical': 8,
            'mileage_high': 500000,
            'truck_age_high': 10,
            'maintenance_cost_warning': 50000,
            'incident_count_critical': 8,
            'profit_margin_warning': 15
        }
        print("AlertsEngine initialized!")
    
    def set_threshold(self, key, value):
        """Update a threshold value"""
        if key in self.thresholds:
            self.thresholds[key] = value
    
    def get_thresholds(self):
        """Returns current threshold settings"""
        return self.thresholds.copy()
    
    def _get_financial_alerts(self):
        """Collect alerts from financial analysis"""
        from financial_analyzer import FinancialAnalyzer
        try:
            analyzer = FinancialAnalyzer(self.data)
            return analyzer.get_alerts()
        except Exception as e:
            print(f"Financial alerts error: {e}")
            return []
    
    def _get_operational_alerts(self):
        """Collect alerts from operational analysis"""
        from Operational_Efficiency import OperationalAnalyzer
        try:
            analyzer = OperationalAnalyzer(self.data)
            return analyzer.get_alerts()
        except Exception as e:
            print(f"Operational alerts error: {e}")
            return []
    
    def _get_driver_alerts(self):
        """Collect alerts from driver performance analysis"""
        from driver_analyzer import DriverPerformanceAnalyzer
        try:
            analyzer = DriverPerformanceAnalyzer(self.data)
            return analyzer.get_alerts()
        except Exception as e:
            print(f"Driver alerts error: {e}")
            return []
    
    def _get_fleet_alerts(self):
        """Collect alerts from fuel/maintenance analysis"""
        from fuel_maintenance import FuelMaintenanceAnalyzer
        try:
            analyzer = FuelMaintenanceAnalyzer(self.data)
            return analyzer.get_alerts()
        except Exception as e:
            print(f"Fleet alerts error: {e}")
            return []
    
    def get_all_alerts(self):
        """
        Collects and combines alerts from all analyzer modules.
        Returns a list of alert dictionaries with type, title, message, metric, and source.
        """
        all_alerts = []
        
        # Collect from each source
        sources = [
            ('Financial', self._get_financial_alerts),
            ('Operations', self._get_operational_alerts),
            ('Drivers', self._get_driver_alerts),
            ('Fleet', self._get_fleet_alerts)
        ]
        
        for source_name, get_alerts_func in sources:
            try:
                alerts = get_alerts_func()
                for alert in alerts:
                    alert['source'] = source_name
                    alert['timestamp'] = datetime.now().isoformat()
                    all_alerts.append(alert)
            except Exception as e:
                print(f"Error collecting {source_name} alerts: {e}")
        
        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        all_alerts.sort(key=lambda x: severity_order.get(x.get('type', 'info'), 3))
        
        return all_alerts
    
    def get_critical_alerts(self):
        """Returns only critical-level alerts"""
        return [a for a in self.get_all_alerts() if a.get('type') == 'critical']
    
    def get_warning_alerts(self):
        """Returns only warning-level alerts"""
        return [a for a in self.get_all_alerts() if a.get('type') == 'warning']
    
    def get_info_alerts(self):
        """Returns only info-level alerts"""
        return [a for a in self.get_all_alerts() if a.get('type') == 'info']
    
    def get_alert_count(self):
        """Returns count of alerts by severity for badge display"""
        all_alerts = self.get_all_alerts()
        return {
            'total': len(all_alerts),
            'critical': len([a for a in all_alerts if a.get('type') == 'critical']),
            'warning': len([a for a in all_alerts if a.get('type') == 'warning']),
            'info': len([a for a in all_alerts if a.get('type') == 'info'])
        }
    
    def get_alerts_by_source(self, source):
        """Returns alerts filtered by source module"""
        return [a for a in self.get_all_alerts() if a.get('source') == source]
    
    def get_alerts_summary(self):
        """Returns a summary of all alerts for dashboard display"""
        counts = self.get_alert_count()
        critical = self.get_critical_alerts()
        
        summary = {
            'counts': counts,
            'top_critical': critical[:3] if critical else [],
            'needs_attention': counts['critical'] > 0 or counts['warning'] > 2,
            'status': 'Critical' if counts['critical'] > 0 else 'Warning' if counts['warning'] > 0 else 'Good'
        }
        
        return summary
    
    def format_alert_for_display(self, alert):
        """Formats an alert for Streamlit display with icons"""
        type_icons = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🟢'
        }
        
        source_icons = {
            'Financial': '💰',
            'Operations': '⏱️',
            'Drivers': '👨‍✈️',
            'Fleet': '⛽'
        }
        
        return {
            'icon': type_icons.get(alert.get('type'), '⚪'),
            'source_icon': source_icons.get(alert.get('source'), '📊'),
            'title': alert.get('title', 'Alert'),
            'message': alert.get('message', ''),
            'metric': alert.get('metric', ''),
            'source': alert.get('source', 'Unknown'),
            'type': alert.get('type', 'info')
        }
    
    def get_formatted_alerts(self):
        """Returns all alerts formatted for display"""
        return [self.format_alert_for_display(a) for a in self.get_all_alerts()]


class AlertThresholdConfig:
    """
    Helper class for managing alert thresholds in Settings UI
    """
    
    DEFAULT_THRESHOLDS = {
        'on_time_rate_critical': {'label': 'On-Time Rate (Critical)', 'value': 85, 'unit': '%'},
        'on_time_rate_warning': {'label': 'On-Time Rate (Warning)', 'value': 90, 'unit': '%'},
        'idle_hours_warning': {'label': 'Idle Hours (Warning)', 'value': 5, 'unit': 'hrs'},
        'fleet_mpg_warning': {'label': 'Fleet MPG (Warning)', 'value': 6.0, 'unit': 'MPG'},
        'downtime_hours_critical': {'label': 'Downtime (Critical)', 'value': 8, 'unit': 'hrs'},
        'mileage_high': {'label': 'High Mileage Alert', 'value': 500000, 'unit': 'miles'},
        'truck_age_high': {'label': 'High Age Alert', 'value': 10, 'unit': 'years'},
        'maintenance_cost_warning': {'label': 'Maintenance Cost (Warning)', 'value': 50000, 'unit': '$'},
        'incident_count_critical': {'label': 'Incident Count (Critical)', 'value': 8, 'unit': 'count'},
        'profit_margin_warning': {'label': 'Profit Margin (Warning)', 'value': 15, 'unit': '%'}
    }
    
    @classmethod
    def get_all_configs(cls):
        """Returns all threshold configurations for settings UI"""
        return cls.DEFAULT_THRESHOLDS
    
    @classmethod
    def get_config(cls, key):
        """Returns configuration for a specific threshold"""
        return cls.DEFAULT_THRESHOLDS.get(key, {})
