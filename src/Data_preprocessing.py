# data_preprocessor.py
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self, data_engine):
        self.engine = data_engine
        self.processed_data = {}

    def run_pipeline(self):
        if not self.engine.data:
            print("Loading data first...")
            self.engine.load_all_data()

        print("\nCleaning and preprocessing all tables...\n")
        for table_name, df in self.engine.data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                cleaned = self.clean_table(table_name, df.copy())
                self.processed_data[table_name] = cleaned
            else:
                print(f"Skipping {table_name} - empty or not a DataFrame")

        print(f"\nSuccessfully processed {len(self.processed_data)} tables!")
        return self.processed_data

    def clean_table(self, table_name, df):
        print(f"Processing {table_name}... ({len(df)} rows)")

        # 1. Clean column names
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]

        # 2. Fix dates - SAFELY
        df = self._fix_dates(df)


        # 3. Handle missing values
        # Fill numeric columns with mean, skipping IDs
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            
            if col.endswith('_id') or col.endswith('Id') or col.lower() == 'id':
                continue

            if df[col].isnull().any():
                mean_val = df[col].mean()
                df[col].fillna(mean_val, inplace=True)

        # Drop rows with missing text/categorical data
        object_cols = df.select_dtypes(include=['object']).columns
        if len(object_cols) > 0:
            before = len(df)
            df.dropna(subset=object_cols, inplace=True)
            after = len(df)
            if before > after:
                print(f"   -> Removed {before - after} rows with missing text data")

        # 4. Remove duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            df.drop_duplicates(inplace=True)
            print(f"   -> Removed {duplicates} duplicate rows")

        df.reset_index(drop=True, inplace=True)
        print(f"   -> Final: {len(df)} rows\n")
        return df

    def _fix_dates(self, df):
        # Only try to convert columns that have date-related names
        date_keywords = ['date', 'time', 'dt', 'timestamp', 'datetime', 'year']

        for col in df.columns:
            if any(keyword in col.lower() for keyword in date_keywords):
                # Only convert if it's NOT already numeric
                if not np.issubdtype(df[col].dtype, np.number):
                    # And only if it's string/object type
                    if df[col].dtype == 'object':
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    # If it's already datetime, leave it
        return df