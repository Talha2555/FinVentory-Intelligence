# 🚀 FinVentory Intelligence

**A Smart Business Analytics & Predictive Inventory System**
*Developed for the Database Systems Course at FAST NUCES Karachi.*

## 📖 Overview
FinVentory is a full-stack FinTech application designed to eliminate data blind spots for SMEs. It utilizes a highly normalized PostgreSQL database (4NF) integrated with a Python Streamlit frontend to provide real-time inventory tracking, role-based access control, and AI-weighted demand forecasting.

## ✨ Key Features
* **PostgreSQL Triggers & Automation:** Automated logging of transactions and inventory syncing.
* **Predictive Intelligence:** A 3-month weighted moving average algorithm to forecast product demand.
* **ACID Transactions:** Ensures data integrity across sales and purchases.
* **Live Dashboard:** Interactive UI built with Streamlit, Pandas, and Matplotlib.

## 🚀 How to Run Locally
1. Clone this repository.
2. Create the database: Run `finventory_db.sql` in pgAdmin 4.
3. Install dependencies: `pip install -r requirements.txt`
4. Update `app.py`: Insert your local Postgres password.
5. Launch the app: `streamlit run app.py`

*Contributors: Talha Khan, Muhammad Siraj, Muhammad Furqan, Maaz Umer*