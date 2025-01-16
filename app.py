import streamlit as st
import pandas as pd
import plotly.express as px
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import random

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
            "Balance": round(float(account_info[0]["balance"]), 2),
            "Unrealized PNL": round(float(margin_info["totalUnrealizedProfit"]), 2),
            "Margin Balance": round(float(margin_info["totalMarginBalance"]), 2),
            "Available Balance": round(float(margin_info["availableBalance"]), 2),
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
                "Price": trade["price"],
                "Quantity": trade["qty"],
                "PNL": trade["realizedPnl"],
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
                "Size": pos["positionAmt"],
                "Entry Price": pos["entryPrice"],
                "Mark Price": pos.get("markPrice", "N/A"),
                "PNL": pos["unrealizedProfit"],
            }
            for pos in account_info["positions"]
            if float(pos["positionAmt"]) != 0
        ]
        return pd.DataFrame(positions)
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching positions: {e}")
        return pd.DataFrame()

# Fetching top profit and loss positions
def get_top_positions():
    try:
        positions_data = fetch_positions()
        if positions_data.empty:
            return pd.DataFrame(), pd.DataFrame()
        positions_data["PNL"] = positions_data["PNL"].astype(float)
        top_profit = positions_data.nlargest(5, "PNL")
        top_loss = positions_data.nsmallest(5, "PNL")
        return top_profit, top_loss
    except Exception as e:
        st.error(f"Error fetching top positions: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Fetching open orders
def fetch_open_orders():
    try:
        orders = client.futures_get_open_orders()
        open_orders = [
            {
                "Symbol": order["symbol"],
                "Price": order["price"],
                "Quantity": order["origQty"],
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

# Fetching order history
def fetch_order_history():
    try:
        history = client.futures_account_trades()
        order_history = [
            {
                "Symbol": trade["symbol"],
                "Side": trade["side"],
                "Price": trade["price"],
                "Quantity": trade["qty"],
                "Commission": trade["commission"],
                "Time": pd.to_datetime(trade["time"], unit="ms"),
            }
            for trade in history
        ]
        return pd.DataFrame(order_history)
    except (BinanceAPIException, BinanceRequestException) as e:
        st.error(f"Error fetching order history: {e}")
        return pd.DataFrame()

# Sample Daily PNL Data for Graphs
def generate_sample_pnl_data():
    dates = pd.date_range(start="2025-01-01", end="2025-01-15", freq="D")
    pnl_data = {
        "Date": dates,
        "Daily PNL": [random.uniform(-50, 50) for _ in dates],
        "Cumulative PNL": [sum(random.uniform(-50, 50) for _ in range(i)) for i in range(len(dates))],
    }
    return pd.DataFrame(pnl_data)

# Graph functions
def plot_daily_pnl(data):
    fig = px.bar(data, x="Date", y="Daily PNL", title="Daily PNL", color="Daily PNL", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

def plot_cumulative_pnl(data):
    fig = px.line(data, x="Date", y="Cumulative PNL", title="Cumulative PNL", markers=True)
    st.plotly_chart(fig, use_container_width=True)

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
    order_history_data = fetch_order_history()
    if not order_history_data.empty:
        st.dataframe(order_history_data, use_container_width=True)
    else:
        st.warning("No order history available.")

elif choice == "Trade History":
    st.subheader("Trade History")
    trade_history_data = fetch_trade_history()
    if not trade_history_data.empty:
        st.dataframe(trade_history_data, use_container_width=True)
        st.markdown("### Top 5 Profit-Making Positions")
        top_profit, top_loss = get_top_positions()
        if not top_profit.empty:
            st.dataframe(top_profit, use_container_width=True)
        else:
            st.warning("No profit-making positions found.")
        st.markdown("### Top 5 Loss-Making Positions")
        if not top_loss.empty:
            st.dataframe(top_loss, use_container_width=True)
        else:
            st.warning("No loss-making positions found.")
    else:
        st.warning("No trade history available.")

elif choice == "Analytics":
    st.subheader("Analytics")
    pnl_data = generate_sample_pnl_data()
    st.markdown("### Daily PNL")
    plot_daily_pnl(pnl_data)
    st.markdown("### Cumulative PNL")
    plot_cumulative_pnl(pnl_data)

# Footer
st.markdown("---")
st.text("'The legacy of those who build is carried forward in what they create.'")
