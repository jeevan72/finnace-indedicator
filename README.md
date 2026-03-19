# 📈 Financial Intelligence Terminal

A **personal financial intelligence terminal** for India-focused commodity, equity, and macro research. It aggregates real-time prices, NSE derivatives data, EIA supply signals, BSE corporate actions, trade flows, sanctions, and macro indicators into a unified CLI dashboard and a Streamlit GUI, all backed by a local SQLite database.

## ✨ Features

- **Live Market Data:** Fetches prices for top commodities (Gold, Silver, WTI, Brent), indices (Nifty, Sensex, S&P 500), and forex.
- **Indian Market Accuracy:** Automatically converts USD-denominated precious metals (like COMEX Gold/Silver) into **INR per 10 grams** applying India's local import duties/GST premiums for accurate domestic pricing.
- **Top Commodities Tracking:** Visual Streamlit dashboard featuring horizontal bar charts and KPI metrics for the biggest market movers.
- **Macro & Supply Signals:** Pulls data from EIA (Crude inventory), FRED & World Bank (CPI, GDP, Interest rates).
- **Options Analytics:** Calculates Put-Call Ratio (PCR), Max Pain, and Implied Volatility (IV) Rank directly from the NSE options chain.
- **Automated Alerts:** BSE corporate announcements and OFAC sanctions screening.
- **Background Daemon:** Built-in scheduler (`APScheduler`) to silently gather data at regular intervals.

## 🛠️ Tech Stack

- **Python 3.10+**
- **Data Collection:** `yfinance`, `fredapi`, `world-bank-data`, `requests`
- **Database:** `peewee` (SQLite)
- **UI / Dashboard:** `streamlit` (Web GUI), `rich` & `typer` (CLI)
- **Analysis:** `pandas`, `pandas-ta`, `py-vollib`

## 🚀 Quick Start

### 1. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/jeevan72/finnace-indedicator.git
cd finnace-indedicator

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # For Windows
# source venv/bin/activate  # For Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (Optional)
Create a `.env` file in the root directory to enable additional macro/supply data:
```env
FRED_API_KEY=your_key_here
EIA_API_KEY=your_key_here
```
*(Note: Core price fetching from Yahoo Finance, NSE, and BSE works perfectly without any API keys!)*

### 3. Usage

**Start the Web Dashboard:**
```bash
streamlit run src/dashboard/app.py
```

**Use the Command Line Interface (CLI):**
```bash
# View the live prices panel
python main.py prices

# Fetch a specific asset fresh
python main.py fetch-now Gold

# View the full text-based terminal
python main.py dashboard

# Start the background data collector
python main.py daemon
```

## 📂 Architecture overview

- `src/fetchers/`: Modules connecting to APIs (Yahoo, NSE, BSE, FRED).
- `src/analysis/`: Modules calculating option Greeks, hedging signals, and supply risk.
- `src/storage/`: SQLite database models and setup.
- `src/dashboard/`: The Streamlit graphical web application.
- `src/cli/`: The terminal application using Rich panels.

## 📄 License
This project is open-source and available under the MIT License.
