import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="FinVentory Intelligence", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

# ==========================================
# 2. DATABASE CONNECTION
# ==========================================
DB_HOST = "localhost"
DB_NAME = "finventory_db"
DB_USER = "postgres"
DB_PASS = "your_local_password_here"  # Your password
DB_PORT = "5432"


@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def fetch_data(query):
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        return df
    return pd.DataFrame()


# Function for executing updates (like the Alert Trigger)
def execute_query(query):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            st.error(f"Query execution failed: {e}")
            return False


# ==========================================
# 3. AUTHENTICATION (CSV)
# ==========================================
def authenticate(username, password):
    try:
        users_df = pd.read_csv("users.csv")
        match = users_df[(users_df['username'] == username) & (users_df['password'] == password)]
        if not match.empty:
            return match.iloc[0]['role']
        return None
    except FileNotFoundError:
        st.error("Error: users.csv file not found.")
        return None


# ==========================================
# 4. USER INTERFACE
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 FinVentory Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            role = authenticate(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.success(f"Welcome! Logged in as {role}")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

else:
    # Sidebar Navigation
    st.sidebar.title("FinVentory Hub")
    st.sidebar.write(f"**Current Role:** {st.session_state.role}")

    menu_options = ["Dashboard", "Inventory & Alerts", "AI Demand Predictions"]
    if st.session_state.role == "Admin":
        menu_options.extend(["Profit & Loss", "Transactions"])

    choice = st.sidebar.radio("Navigate", menu_options)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    # --- PAGE: DASHBOARD ---
    if choice == "Dashboard":
        st.title("📊 Financial & Performance Dashboard")

        # Top Metrics Columns
        st.subheader("Top Performers")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Top Products")
            df_top_prod = fetch_data("SELECT * FROM top_products;")
            st.dataframe(df_top_prod, hide_index=True)

        with col2:
            st.markdown("### Top Suppliers")
            df_top_sup = fetch_data("SELECT * FROM top_suppliers;")
            st.dataframe(df_top_sup, hide_index=True)

        with col3:
            st.markdown("### Top Retailers")
            df_top_ret = fetch_data("SELECT * FROM top_retailers;")
            st.dataframe(df_top_ret, hide_index=True)

        st.divider()

        # Monthly Sales Trend
        st.subheader("Revenue Trend Over Time")
        df_sales = fetch_data("SELECT * FROM monthly_sales_view;")
        if not df_sales.empty:
            fig, ax = plt.subplots(figsize=(10, 3))
            sns.lineplot(data=df_sales, x='month', y='revenue', marker='o', color='#2E86C1', ax=ax)
            plt.xticks(rotation=45)
            st.pyplot(fig)

    # --- PAGE: AI DEMAND PREDICTIONS ---
    elif choice == "AI Demand Predictions":
        st.title("🤖 AI-Weighted Demand Forecast")
        st.write("Using a weighted algorithm (50% current, 30% prev, 20% prev-2) to forecast upcoming inventory needs.")

        df_predict = fetch_data("SELECT * FROM demand_prediction_view ORDER BY predicted_sales DESC;")

        if not df_predict.empty:
            col1, col2 = st.columns([2, 3])

            with col1:
                st.dataframe(df_predict, use_container_width=True, hide_index=True)

            with col2:
                fig, ax = plt.subplots(figsize=(8, 5))
                sns.barplot(data=df_predict, y='name', x='predicted_sales', palette='viridis', ax=ax)
                ax.set_title("Forecasted Unit Sales by Product")
                ax.set_xlabel("Predicted Units Needed")
                ax.set_ylabel("")
                st.pyplot(fig)
        else:
            st.info("Insufficient historical data to generate AI predictions.")

    # --- PAGE: INVENTORY & ALERTS ---
    elif choice == "Inventory & Alerts":
        st.title("📦 Inventory Status & System Alerts")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Current Stock Levels")
        with col2:
            # The interactive trigger button
            if st.button("🚨 Run System Alert Check"):
                success = execute_query("UPDATE inventory SET quantity = quantity;")
                if success:
                    st.success("System scanned. Alerts updated.")
                    st.rerun()

        df_inventory = fetch_data("SELECT * FROM inventory_status_view;")
        if not df_inventory.empty:
            st.dataframe(df_inventory, use_container_width=True)

        st.divider()

        st.subheader("Active Alerts")
        df_alerts = fetch_data("SELECT * FROM alerts WHERE status = 'UNREAD' ORDER BY created_at DESC;")
        if not df_alerts.empty:
            for index, row in df_alerts.iterrows():
                if row['alert_type'] == 'LOW_STOCK':
                    st.warning(f"🕒 {row['created_at']} | **{row['alert_type']}** - {row['message']}")
                else:
                    st.error(f"🕒 {row['created_at']} | **{row['alert_type']}** - {row['message']}")
        else:
            st.success("No unread system alerts. All systems nominal.")

    # --- PAGE: PROFIT & LOSS (ADMIN ONLY) ---
    elif choice == "Profit & Loss":
        st.title("💰 Comprehensive Financial Summary")
        # Updated to the new profit_loss_summary view
        df_profit = fetch_data("SELECT * FROM profit_loss_summary;")

        if not df_profit.empty:
            st.markdown("### Executive Breakdown")

            # 4 Columns for the new breakdown
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"Rs. {df_profit['total_revenue'].iloc[0]:,.2f}")
            c2.metric("Total Cost", f"Rs. {df_profit['total_cost'].iloc[0]:,.2f}")
            c3.metric("Gross Profit", f"Rs. {df_profit['gross_profit'].iloc[0]:,.2f}")
            c4.metric("Total Expenses", f"Rs. {df_profit['total_expenses'].iloc[0]:,.2f}")

            st.divider()

            # Giant Net Profit Display
            net_profit = df_profit['net_profit'].iloc[0]
            profit_color = "green" if net_profit >= 0 else "red"
            st.markdown(
                f"<h2 style='text-align: center; color: {profit_color};'>Net Profit/Loss: Rs. {net_profit:,.2f}</h2>",
                unsafe_allow_html=True)

            st.subheader("Financial Distribution")
            sizes = [df_profit['gross_profit'].iloc[0], df_profit['total_cost'].iloc[0],
                     df_profit['total_expenses'].iloc[0]]
            # Filter out negative or zero values for the pie chart
            labels = ['Gross Profit', 'COGS (Cost of Goods)', 'Expenses']
            valid_sizes = [s for s in sizes if s > 0]
            valid_labels = [l for s, l in zip(sizes, labels) if s > 0]

            if valid_sizes:
                fig, ax = plt.subplots(figsize=(4, 4))
                ax.pie(valid_sizes, labels=valid_labels, autopct='%1.1f%%', startangle=90,
                       colors=['#2ecc71', '#e74c3c', '#f1c40f'])
                ax.axis('equal')
                st.pyplot(fig)
        else:
            st.info("No financial data available.")

    # --- PAGE: TRANSACTIONS (ADMIN ONLY) ---
    elif choice == "Transactions":
        st.title("🔄 Full Transaction Ledger")
        st.write("All auto-recorded sales and purchases via trigger integration.")

        query = """
        SELECT 
            t.transaction_id,
            t.transaction_type,
            COALESCE(r.name, s.name, 'N/A') AS party_name,
            t.amount,
            t.transaction_date
        FROM transactions t
        LEFT JOIN retailers r ON t.retailer_id = r.retailer_id
        LEFT JOIN suppliers s ON t.supplier_id = s.supplier_id
        ORDER BY t.transaction_date DESC LIMIT 100;
        """
        df_trans = fetch_data(query)
        st.dataframe(df_trans, use_container_width=True)