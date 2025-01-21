import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Set Streamlit page configuration
st.set_page_config(page_title="Binance Our Dashboard", layout="wide")

# Flask API Server URL
API_SERVER = "http://34.47.211.154:5000"  # Replace with your AWS server IP

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/4b/Binance_logo.png", width=200)
st.sidebar.title("Binance Our Dashboard")
menu = ["Account Summary", "Positions", "Open Orders", "Order History", "Trade History", "Analytics"]
choice = st.sidebar.radio("Navigation", menu)

# Helper functions to fetch data from Flask API
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_SERVER}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

# Rendering sections
if choice == "Account Summary":
    st.subheader("Account Summary")
    account_summary = fetch_data("account_summary")
    if account_summary:
        st.metric(label="Balance", value=f"{account_summary['Balance']} USDT")
        st.metric(label="Unrealized PNL", value=f"{account_summary['Unrealized PNL']} USDT")
        st.metric(label="Margin Balance", value=f"{account_summary['Margin Balance']} USDT")
        st.metric(label="Available Balance", value=f"{account_summary['Available Balance']} USDT")

elif choice == "Positions":
    st.subheader("Positions")
    positions_data = fetch_data("positions")
    if positions_data:
        df = pd.DataFrame(positions_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No positions found.")

elif choice == "Open Orders":
    st.subheader("Open Orders")
    open_orders_data = fetch_data("open_orders")
    if open_orders_data:
        df = pd.DataFrame(open_orders_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No open orders found.")

elif choice == "Order History":
    st.subheader("Order History")
    trade_history_data = fetch_data("trade_history")
    if trade_history_data:
        df = pd.DataFrame(trade_history_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No order history available.")

elif choice == "Analytics":
    st.subheader("Analytics")
    pnl_data = fetch_data("pnl_analytics")
    if pnl_data:
        df = pd.DataFrame(pnl_data)
        if not df.empty:
            # Advanced Analytics: Plot graphs
            st.markdown("### Advanced Analytics")

            # Daily PNL Bar Chart
            daily_fig = px.bar(
                df, x="Date", y="PNL", title="Daily PNL", color="PNL", color_continuous_scale="RdYlGn",
                labels={"PNL": "Profit/Loss (USDT)", "Date": "Date"}
            )
            st.plotly_chart(daily_fig, use_container_width=True)

            # Cumulative PNL Line Chart
            df['Cumulative PNL'] = df['PNL'].cumsum()
            cumulative_fig = px.line(
                df, x="Date", y="Cumulative PNL", title="Cumulative PNL",
                labels={"Cumulative PNL": "Cumulative Profit/Loss (USDT)", "Date": "Date"}, markers=True
            )
            st.plotly_chart(cumulative_fig, use_container_width=True)

            # Interactive Scatter Plot
            scatter_fig = px.scatter(
                df, x="Date", y="PNL", color="PNL",
                title="Scatter Plot of PNL Over Time",
                labels={"PNL": "Profit/Loss (USDT)", "Date": "Date"},
                hover_data=["PNL"],
            )
            st.plotly_chart(scatter_fig, use_container_width=True)
        else:
            st.warning("No PNL data available.")
    else:
        st.warning("No PNL data available.")

# Footer
st.markdown("---")
st.text("")
