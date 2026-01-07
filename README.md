<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🚚 FleetSmart Analytics</h1>
<h3 align="center">Logistics Operations Analytics Dashboard</h3>

<p align="center">
  <strong>A comprehensive fleet management and logistics analytics platform built with Python and Streamlit</strong>
</p>

---

## 📋 Overview

**FleetSmart Analytics** is an enterprise-grade logistics operations dashboard that provides real-time insights into fleet performance, driver efficiency, fuel consumption, maintenance costs, and delivery reliability. Built for logistics managers and operations teams who need data-driven decision making.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Financial Analytics** | Revenue tracking, profit margins, route profitability, cost-per-mile analysis |
| ⏱️ **Operational Efficiency** | On-time delivery rates, fleet utilization, delay analysis |
| 👨‍✈️ **Driver Performance** | Performance scoring, leaderboards, safety metrics |
| ⛽ **Fleet Cost Management** | Fuel consumption trends, maintenance costs, truck risk assessment |
| 🔔 **Smart Alerts** | Automated alerts for KPI thresholds and anomalies |
| 📈 **Predictive Insights** | Seasonality patterns, risk forecasting, trend analysis |

---

## 🖥️ Dashboard Preview

### Overview Page
```
┌─────────────────────────────────────────────────────────────┐
│  🏠 Fleet Operations Overview                               │
├───────────────┬───────────────┬─────────────────────────────┤
│ 💰 Revenue    │ 📈 Profit     │ ⏱️ On-Time Rate             │
│ $2.5M        │ $450K         │ 89.2%                       │
├───────────────┴───────────────┴─────────────────────────────┤
│ 🚨 Active Alerts Ticker                                     │
├─────────────────────────────────────────────────────────────┤
│ 📊 Monthly Performance Trend [Chart]                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Gith027/FleetSmart-Analytics-Logistics-Operations-Analytics-Dashboard.git
   cd FleetSmart-Analytics-Logistics-Operations-Analytics-Dashboard
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   cd src
   streamlit run app.py
   ```

5. **Open in browser**
   ```
   http://localhost:8501
   ```

---

## 📁 Project Structure

```
FleetSmart-Analytics/
│
├── 📂 src/                          # Source code
│   ├── app.py                       # Streamlit web application
│   ├── data_loader.py               # CSV data loading engine
│   ├── Data_preprocessing.py        # Data cleaning pipeline
│   ├── financial_analyzer.py        # Financial analytics module
│   ├── Operational_Efficiency.py    # Operations analytics module
│   ├── driver_analyzer.py           # Driver performance module
│   ├── fuel_maintenance.py          # Fleet costs module
│   ├── alerts_engine.py             # Centralized alert system
│   ├── Visualization.py             # Advanced visualizations
│   └── Main_dashboard.py            # CLI interface (optional)
│
├── 📂 Data files/                   # Sample data (CSV files)
│   ├── drivers.csv
│   ├── trucks.csv
│   ├── loads.csv
│   ├── trips.csv
│   ├── fuel_purchases.csv
│   ├── maintenance_records.csv
│   └── ... (14 CSV files total)
│
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── CODE_DOCUMENTATION.md            # Detailed code documentation
```

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 **Overview** | Real-time KPIs, alerts ticker, monthly trends |
| 💰 **Financial** | Revenue analysis, route profitability, cost trends |
| ⏱️ **Operations** | On-time delivery, fleet utilization, delay analysis |
| 👨‍✈️ **Drivers** | Performance leaderboard, scoring, safety metrics |
| ⛽ **Fleet Costs** | Fuel/maintenance costs, high-risk truck detection |
| 📈 **Predictive** | Profit distribution, seasonality, risk forecasting |
| ⚠️ **Alerts** | Centralized alert management with filtering |
| ⚙️ **Settings** | Threshold configuration, export options |
| ℹ️ **Info** | Application information and support |

---

## 🔧 Configuration

### Alert Thresholds

Customize alert thresholds in the **Settings** page:

| Threshold | Default | Description |
|-----------|---------|-------------|
| On-Time Rate (Critical) | 85% | Triggers critical alert |
| On-Time Rate (Warning) | 90% | Triggers warning |
| Fleet MPG (Warning) | 6.0 | Low fuel efficiency alert |
| High Mileage Alert | 500,000 mi | Truck maintenance risk |
| Truck Age Alert | 10 years | Aging fleet warning |
| Maintenance Cost | $50,000 | High spend warning |

---

## 📦 Dependencies

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
openpyxl>=3.1.0
```

---

## 🗃️ Data Requirements

The application expects CSV files in the `Data files/` directory:

| File | Required Columns |
|------|-----------------|
| `drivers.csv` | driver_id, first_name, last_name |
| `trucks.csv` | truck_id, unit_number, model_year, odometer_reading |
| `loads.csv` | load_id, load_date, revenue, customer_id |
| `trips.csv` | trip_id, load_id, truck_id, driver_id, dispatch_date |
| `routes.csv` | route_id, origin_city, destination_city |
| `fuel_purchases.csv` | truck_id, gallons, total_cost, price_per_gallon |
| `maintenance_records.csv` | truck_id, total_cost, downtime_hours |
| `delivery_events.csv` | load_id, scheduled_datetime, actual_datetime |
| `driver_monthly_metrics.csv` | driver_id, month, total_revenue, average_mpg |
| `truck_utilization_metrics.csv` | truck_id, month, utilization_rate |
| `safety_incidents.csv` | driver_id, incident_date |

---

## 🛠️ Development

### Running the CLI Version

```bash
cd src
python Main_dashboard.py
```

### Running Tests
```bash
python -m pytest tests/
```

---

## 📈 Key Metrics Calculated

| Metric | Formula |
|--------|---------|
| **Profit** | Revenue - Fuel Surcharge - Accessorial Charges |
| **Profit Margin %** | (Profit / Revenue) × 100 |
| **Cost Per Mile** | (Fuel + Accessorial) / Distance |
| **On-Time Flag** | Actual Time ≤ Scheduled + 30 min |
| **Driver Score** | Revenue×0.5 + MPG×4 + OTD×40 - Idle×3 - Incidents×15 |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Support

For questions or support:
- **Email**: support@fleetsmart-analytics.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/FleetSmart-Analytics/issues)

---

<p align="center">
  <strong>Built with ❤️ for Logistics Excellence</strong>
</p>

<p align="center">
  © 2026 FleetSmart Analytics. All rights reserved.
</p>
