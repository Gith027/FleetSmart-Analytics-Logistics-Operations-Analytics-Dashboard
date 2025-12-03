import pandas as pd
import numpy as np
from data_loader import DataEngine
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self, data_engine):
        self.engine = data_engine
        self.processed_data = {}
    
    def run_pipeline(self):
        # Ensure data is loaded
        if not hasattr(self.engine, 'data') or not self.engine.data:
            if hasattr(self.engine, 'load_all_data'):
                self.engine.load_all_data()
            else:
                raise AttributeError("data_engine must have .data dict or .load_all_data() method")
        
        # Clean each table
        for table_name, df in self.engine.data.items():
            if not isinstance(df, pd.DataFrame):
                print(f"Warning: {table_name} is not a DataFrame, skipping...")
                continue
            cleaned_df = self.clean_table(table_name, df.copy())
            self.processed_data[table_name] = cleaned_df
        
        print(f"\nSuccessfully processed {len(self.processed_data)} tables.")
        return self.processed_data
    
    def clean_table(self, table_name, df):
        df = df.copy()
        
        # 1. Clean column names
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # 2. Fix dates
        df = self._fix_dates(df)
        
        # 3. Handle missing values
        df = self._handle_missing(df, table_name)
        
        # 4. Remove duplicates
        duplicates_removed = df.duplicated().sum()
        df = df.drop_duplicates().reset_index(drop=True)
        
        if duplicates_removed > 0:
            print(f" Removed {duplicates_removed} duplicates from {table_name}")
        
        return df
    
    def _fix_dates(self, df):
        date_keywords = ['date', 'time', 'year', 'dt', 'timestamp']
        for col in df.columns:
            if any(keyword in col.lower() for keyword in date_keywords):
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    
    def _handle_missing(self, df, table_name):
        original_rows = len(df)  
        
        # 1. Handle numeric columns (fill with mean)
        numeric_cols = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]
        for col in numeric_cols:
            missing = df[col].isnull().sum()
            if missing > 0:
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                print(f"Filled {missing} missing numeric values in {table_name}.{col} with mean ({mean_val:.2f})")

        # 2. Handle categorical columns → REMOVE ROWS if missing
        categorical_cols = [col for col in df.columns if df[col].dtype.kind in 'ObSU']

        if categorical_cols:
            missing_in_cat = df[categorical_cols].isnull().any(axis=1)
            rows_to_drop = missing_in_cat.sum()
            if rows_to_drop > 0:
                print(f"Removing {rows_to_drop} rows from {table_name} due to missing categorical values")
                df = df[~missing_in_cat].reset_index(drop=True)
            else:
                print(f"No missing categorical values in {table_name}")
        else:
            print(f"No categorical columns found in {table_name}")

        final_rows = len(df)
        print(f"Rows: {original_rows} -> {final_rows} (removed {original_rows - final_rows})\n")
        
        return df


# === RUN IT ===
if __name__ == "__main__":
    engine = DataEngine()
    prep = DataPreprocessor(engine)
    result = prep.run_pipeline()
    
    # Optional: See final shapes
    print("\nFinal dataset sizes after cleaning:")
    for name, df in result.items():
        print(f"  {name}: {df.shape}")