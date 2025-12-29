# main_dashboard.py - FINAL INTERACTIVE DASHBOARD (100% WORKING)
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from financial_analyzer import FinancialAnalyzer
from Operational_Efficiency import OperationalAnalyzer
from fuel_maintenance import FuelMaintenanceAnalyzer
from driver_analyzer import DriverPerformanceAnalyzer
from Visulization import PredictiveInsights

def main():
    print("\n" + "="*80)
    print("        FLEETSMART LOGISTICS ANALYTICS DASHBOARD")
    print("                Intelligent Fleet Management System")
    print("="*80)

    # Auto Load & Clean Data
    print("\nInitializing... Loading all data (this may take a moment)...")
    engine = DataEngine("data files/")
    prep = DataPreprocessor(engine)
    data = prep.run_pipeline()

    finance = FinancialAnalyzer(data)
    finance_df = finance._prepare_data()

    ops = OperationalAnalyzer(data)
    ops_df = ops._prepare_data()

    print("System ready! All data loaded and processed.")
    print("="*80)

    while True:
        print("\n" + " WHAT DO YOU WANT TO SEE? ".center(80, "="))
        print("1. Financial Performance Summary")
        print("2. On-Time Delivery Performance")
        print("3. Top Performing Drivers")
        print("4. Fual Maintain Analysis")
        print("5. Predictive Insights")
        print("6. Exit")
        print("="*80)
        
        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            print("\n" + "-"*70)
            print(" FINANCIAL PERFORMANCE REPORT ")
            print("-"*70)
            finance.show_dashboard()

        elif choice == '2':
            print("\n" + "-"*70)
            print(" ON-TIME DELIVERY ANALYSIS ")
            print("-"*70)
            ops.show_dashboard()
            

        elif choice == '3':
            print("\n" + "-"*70)
            print(" DRIVER PERFORMANCE LEADERBOARD ")
            print("-"*70)
            DriverPerformanceAnalyzer(data).show_dashboard()

        elif choice == '4':
            print("\n" + "-"*70)
            print(" Fual Maintain Analysis ")
            print("-"*70)
            FuelMaintenanceAnalyzer(data).show_dashboard()

        elif choice == '5':
            print("\n" + "="*80)
            print(" predictive Insights ")
            print("="*80)
            PredictiveInsights(data).show_insights()
            

        elif choice in ['6', 'exit', 'q']:
            print("\nThank you for using FleetSmart Analytics!")
            print("Have a productive day!")
            break

        else:
            print("Invalid option. Please choose 1–6.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()