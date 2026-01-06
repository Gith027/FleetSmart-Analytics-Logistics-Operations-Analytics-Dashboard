import pandas as pd
import os


class DataEngine:
    def __init__(self, data_path=None):
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root, then into "Data files"
        if data_path is None:
            self.data_path = os.path.join(script_dir, "..", "Data files")
        else:
            # If a path is provided, make it absolute relative to project root
            self.data_path = os.path.join(script_dir, "..", data_path)
        self.data_path = os.path.normpath(self.data_path)  # Normalize the path
        self.data = {}  # Empty dictionary to store all loaded tables
    
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
                file_path = os.path.join(self.data_path, f"{file}.csv")
                self.data[file] = pd.read_csv(file_path)
                print(f"Loaded {file}: {self.data[file].shape}")
            except FileNotFoundError:
                print(f"Warning: {file}.csv not found")
            except Exception as e:
                # Any other error (corrupted file, wrong format, etc.)
                print(f"Error loading {file}.csv: {e}")
        return self.data

