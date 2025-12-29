# main_dashboard.py
from data_loader import DataEngine
from Data_preprocessing import DataPreprocessor
from financial_analyzer import FinancialAnalyzer
from Operational_Efficiency import OperationalAnalyzer
from fuel_maintenance import FuelMaintenanceAnalyzer
from driver_analyzer import DriverPerformanceAnalyzer
from Visulization import PredictiveInsights

def main():
    print("\n" + "="*80)
    print("         FLEETSMART LOGISTICS ANALYTICS DASHBOARD")
    print("                Intelligent Fleet Management System")
    print("="*80)

    print("\nLoading and cleaning data...")
    engine = DataEngine("data files/")
    preprocessor = DataPreprocessor(engine)
    data = preprocessor.run_pipeline()

    if not data:
        print("No data loaded. Check your 'data files/' folder.")
        return

    # Create analyzers
    finance = FinancialAnalyzer(data)
    ops = OperationalAnalyzer(data)

    print("\nSystem Ready! Choose an option below.\n")

    while True:
        print("="*80)
        print("                    MAIN MENU")
        print("="*80)
        print("1. Financial Performance")
        print("2. Operational Efficiency (On-Time Delivery)")
        print("3. Driver Performance Leaderboard")
        print("4. Fuel & Maintenance Costs")
        print("5. Predictive Insights & Charts")
        print("6. Exit")
        print("="*80)

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            finance.show_dashboard()
        elif choice == '2':
            ops.show_dashboard()
        elif choice == '3':
            DriverPerformanceAnalyzer(data).show_dashboard()
        elif choice == '4':
            FuelMaintenanceAnalyzer(data).show_dashboard()
        elif choice == '5':
            PredictiveInsights(data).show_insights()
        elif choice == '6':
            print("\nThank you for using FleetSmart Analytics!")
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1–6.")

        input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main()