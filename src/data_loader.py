import pandas as pd


class DataEngine:
    def __init__(self,data_path="Data files/"):
        self.data_path = data_path  # Remember where the CSV files are stored
        self.data={}                # Empty dictionary to store all loaded tables
    
    def load_all_data(self):
        
        files_to_load=[
            'drivers', 'trucks', 'trailers', 'customers',
            'facilities', 'routes', 'loads', 'trips',
            'fuel_purchases', 'maintenance_records',
            'delivery_events', 'safety_incidents',
            'driver_monthly_metrics', 'truck_utilization_metrics'
        ]
        for file in files_to_load:
            try:
                self.data[file]=pd.read_csv(f"{self.data_path}{file}.csv")
                print(f"Loaded {file}:{self.data[file].shape}")
            except FileNotFoundError:
                print(f"Warning:{file}.csv not found")
            except Exception as e:
                # Any other error (corrupted file, wrong format, etc.)
                print(f"Error loading {file}.csv: {e}")
        return self.data

