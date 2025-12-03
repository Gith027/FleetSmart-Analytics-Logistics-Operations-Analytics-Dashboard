import pandas as pd


class DataEngine:
    def __init__(self,data_path="data files/"):
        self.data_path = data_path  # Remember where the CSV files are stored
        self.data={}                # Empty dictionary to store all loaded tables
    
    def load_all_data(self):
        """Load all 14 csv Files into memort"""
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

    def get_merged_data(self):
        """Create the main merged dataset for analysis"""
         # Merge loads + trips (core relationship)
        merged = pd.merge(
            self.data['loads'],
            self.data['trips'],
            left_on='load_id',
            right_on='load_id',
            how='inner'
        )
         
        print(f"Merged dataset shape: {merged.shape}")
        return merged

if __name__ == "__main__":
    # Create the engine
    engine = DataEngine(data_path="data files/")  # make sure this folder exists!
    
    # Step 1: Load all CSV files
    print("Loading all data files...")
    engine.load_all_data()
    
    # Step 2: Create the merged dataset
    print("\nCreating merged dataset...")
    df = engine.get_merged_data()
    
    # Now you can analyze!
    print("\nFirst 5 rows:")
    print(df.head())
    
    print("\nColumns:")
    print(df.columns.tolist())
    
    print(f"\nTotal rows in final dataset: {len(df):,}")  