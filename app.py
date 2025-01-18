import streamlit as st
import pandas as pd
import plotly.express as px
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(page_title="Binance Clone Dashboard", layout="wide")

# Testnet API Keys
API_KEY = "715ed9f915fb6ca1e1528205a1bdb4dd5253d855460957a9aa50bca7a100189d"
API_SECRET = "8f1981470f0574e0ad56270ceb0272f9f5ffe0ac29187daf5aacfe28a0084f91"

# Initialize Binance client for Testnet
try:
    client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=True)  # Ensure testnet=True
    st.sidebar.success("Connected to Binance Testnet successfully!")
except Exception as e:
    st.sidebar.error(f"Failed to initialize Binance Testnet client: {e}")
    st.stop()

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/4b/Binance_logo.png", width=200)
st.sidebar.title("Binance Clone Dashboard")
menu = ["Account Summary", "Positions", "Open Orders", "Order History", "Trade History", "Analytics"]
choice = st.sidebar.radio("Navigation", menu)

# Fetching key metrics
def fetch_account_summary():
    try:
        account_info = client.futures_account_balance()
        margin_info = client.futures_account()
        balance_data = {
            "Balance": round(float(account_info[0]["balance"].strip()), 2),
            "Unrealized PNL": round(float(margin_info["totalUnrealizedProfit"].strip()), 2),
            "Margin Balance": round(float(margin_info["totalMarginBalance"].strip()), 2),
            "Available Balance": round(float(margin_info["availableBalance"].strip()), 2),
        }
        return balance_data
    except Exception as e:
        st.error(f"Error fetching account summary: {e}")
        return {
            "Balance": 0,
            "Unrealized PNL": 0,
            "Margin Balance": 0,
            "Available Balance": 0,
        }

# Fetching trade history
def fetch_trade_history():
    try:
        trades = client.futures_account_trades()
        trade_history = [
            {
                "Symbol": trade["symbol"],
                "Side": trade["side"],
                "Price": float(trade["price"]),
                "Quantity": float(trade["qty"]),
                "PNL": float(trade["realizedPnl"]),
                "Time": pd.to_datetime(trade["time"], unit="ms"),
            }
            for trade in trades
        ]
        return pd.DataFrame(trade_history)
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching trade history: {e}")
        return pd.DataFrame()

# Fetching positions
def fetch_positions():
    try:
        account_info = client.futures_account()
        positions = [
            {
                "Symbol": pos["symbol"],
                "Size": float(pos["positionAmt"]),
                "Entry Price": float(pos["entryPrice"]),
                "Mark Price": float(pos.get("markPrice", 0)),
                "PNL": float(pos["unrealizedProfit"]),
            }
            for pos in account_info["positions"]
            if float(pos["positionAmt"]) != 0
        ]
        return pd.DataFrame(positions)
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching positions: {e}")
        return pd.DataFrame()

# Fetching open orders
def fetch_open_orders():
    try:
        orders = client.futures_get_open_orders()
        open_orders = [
            {
                "Symbol": order["symbol"],
                "Price": float(order["price"]),
                "Quantity": float(order["origQty"]),
                "Type": order["type"],
                "Side": order["side"],
                "Status": order["status"],
            }
            for order in orders
        ]
        return pd.DataFrame(open_orders)
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching open orders: {e}")
        return pd.DataFrame()

# Fetching PNL Data and Calculating Metrics
def fetch_pnl_data():
    try:
        trades = client.futures_account_trades()
        pnl_data = [
            {
                "Symbol": trade["symbol"],
                "PNL": float(trade["realizedPnl"]),
                "Date": pd.to_datetime(trade["time"], unit="ms").date(),
            }
            for trade in trades
        ]
        df = pd.DataFrame(pnl_data)
        if df.empty:
            st.warning("No PNL data available.")
            return pd.DataFrame()

        # Group by date and calculate daily PNL
        df_grouped = df.groupby("Date").agg({"PNL": "sum"}).reset_index()
        df_grouped["Cumulative PNL"] = df_grouped["PNL"].cumsum()
        return df_grouped
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching PNL data: {e}")
        return pd.DataFrame()

# Plotting PNL Graphs
def plot_pnl_graphs(df):
    if df.empty:
        st.warning("No data available for plotting.")
        return

    daily_fig = px.bar(
        df, x="Date", y="PNL", title="Daily PNL", color="PNL", color_continuous_scale="RdYlGn",
        labels={"PNL": "Profit/Loss (USDT)", "Date": "Date"}
    )
    st.plotly_chart(daily_fig, use_container_width=True)

    cumulative_fig = px.line(
        df, x="Date", y="Cumulative PNL", title="Cumulative PNL",
        labels={"Cumulative PNL": "Cumulative Profit/Loss (USDT)", "Date": "Date"}, markers=True
    )
    st.plotly_chart(cumulative_fig, use_container_width=True)

# Rendering Sections
if choice == "Account Summary":
    st.subheader("Account Summary")
    account_summary = fetch_account_summary()
    st.metric(label="Balance", value=f"{account_summary['Balance']} USDT")
    st.metric(label="Unrealized PNL", value=f"{account_summary['Unrealized PNL']} USDT")
    st.metric(label="Margin Balance", value=f"{account_summary['Margin Balance']} USDT")
    st.metric(label="Available Balance", value=f"{account_summary['Available Balance']} USDT")

elif choice == "Positions":
    st.subheader("Positions")
    positions_data = fetch_positions()
    if not positions_data.empty:
        st.dataframe(positions_data, use_container_width=True)
    else:
        st.warning("No positions found.")

elif choice == "Open Orders":
    st.subheader("Open Orders")
    open_orders_data = fetch_open_orders()
    if not open_orders_data.empty:
        st.dataframe(open_orders_data, use_container_width=True)
    else:
        st.warning("No open orders found.")

elif choice == "Order History":
    st.subheader("Order History")
    trade_history_data = fetch_trade_history()
    if not trade_history_data.empty:
        st.dataframe(trade_history_data, use_container_width=True)
    else:
        st.warning("No order history available.")

elif choice == "Analytics":
    st.subheader("Analytics")
    pnl_data = fetch_pnl_data()
    if not pnl_data.empty:
        st.markdown("### Daily PNL")
        plot_pnl_graphs(pnl_data)
    else:
        st.warning("No PNL data available.")

# Footer
st.markdown("---")
st.text("'The legacy of those who build is carried forward in what they create.'")
