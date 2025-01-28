import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
import numpy as np

# Configuration
st.set_page_config(
    page_title="Binance Futures Dashboard",
    layout="wide",
    page_icon="📊"
)

# Constants
API_SERVER = "http://34.47.211.154:5000"  
TIMEZONE = pytz.timezone('Asia/Kolkata')

# API Endpoints
ENDPOINTS = {
    "open_positions": "/futures/positions",
    "open_trades": "/futures/open-trades",
    "order_history": "/futures/order-history",
    "trade_history": "/futures/trade-history",
    "position_history": "/futures/position-history",
    "analysis": "/futures/analysis"
}

# Utility Functions
@st.cache_data(ttl=300)
def fetch_data(endpoint, params=None):
    try:
        response = requests.get(f"{API_SERVER}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def format_duration(start, end):
    delta = end - start
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

# Dashboard Components
def render_open_positions():
    st.subheader("📌 Open Positions")
    data = fetch_data(ENDPOINTS["open_positions"])
    
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            # Current Price Simulation
            df['Current Price'] = df['Entry Price'] * (1 + np.random.uniform(-0.05, 0.05, len(df)))
            df['Unrealized PNL'] = (df['Current Price'] - df['Entry Price']) * df['Size']
            
            cols = st.columns([2, 1])
            with cols[0]:
                st.dataframe(
                    df.style.format(precision=2)
                    .background_gradient(subset=['Unrealized PNL'], cmap='RdYlGn')
                    .bar(subset=['Leverage'], color='#5fba7d'),
                    use_container_width=True
                )
            
            with cols[1]:
                fig = px.pie(df, names='Symbol', values='Margin', 
                            title='Margin Distribution')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No open positions found")

def render_trade_history():
    st.subheader("📜 Trade History")
    data = fetch_data(ENDPOINTS["trade_history"])
    
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            df['Time'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                selected_symbol = st.selectbox("Filter by Symbol", ['All'] + list(df['symbol'].unique()))
            with col2:
                date_range = st.date_input("Select Date Range", [])
            
            if selected_symbol != 'All':
                df = df[df['symbol'] == selected_symbol]
            
            if len(date_range) == 2:
                df = df[(df['Time'] >= pd.to_datetime(date_range[0])) & 
                       (df['Time'] <= pd.to_datetime(date_range[1]))]
            
            fig = px.bar(df, x='Time', y='realizedPnl', color='side',
                        title='Realized PNL Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                df.style.format({'realizedPnl': '${:.2f}', 'price': '${:.2f}'})
                .highlight_max(subset=['realizedPnl'], color='#90EE90')
                .highlight_min(subset=['realizedPnl'], color='#FF4747'),
                use_container_width=True
            )

def render_analysis():
    st.subheader("📈 Advanced Analysis")
    data = fetch_data(ENDPOINTS["analysis"])
    
    if data:
        # Key Metrics
        cols = st.columns(4)
        metrics = [
            ("Total PNL", f"${data['totalPnl']:+,.2f}", "#4CAF50"),
            ("Win Rate", f"{data['winRate']:.1%}", "#2196F3"),
            ("Profit Factor", f"{data['profitFactor']:.2f}", "#FF9800"),
            ("Max Drawdown", f"${data['maxDrawdown']:+,.2f}", "#E91E63")
        ]
        
        for col, (label, value, color) in zip(cols, metrics):
            col.markdown(
                f"<div style='padding:15px; background-color:{color}20; border-radius:10px;'>"
                f"<h4 style='color:{color}; margin:0;'>{label}</h4>"
                f"<h2 style='margin:0;'>{value}</h2></div>",
                unsafe_allow_html=True
            )
        
        # PNL Analysis
        pnl_df = pd.DataFrame(data['pnlHistory'])
        pnl_df['date'] = pd.to_datetime(pnl_df['date'])
        
        tabs = st.tabs(["PNL Trend", "Performance Distribution"])
        with tabs[0]:
            fig = px.area(pnl_df, x='date', y='cumulativePnl', 
                         title="Cumulative PNL Trend")
            st.plotly_chart(fig, use_container_width=True)
        
        with tabs[1]:
            fig = px.histogram(pnl_df, x='dailyPnl', nbins=50, 
                             title="Daily PNL Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk Analysis
        st.subheader("Risk Metrics")
        risk_cols = st.columns(3)
        risk_metrics = [
            ("Sharpe Ratio", data['sharpeRatio']),
            ("Sortino Ratio", data['sortinoRatio']),
            ("Volatility", f"{data['volatility']:.2%}")
        ]
        
        for rcol, (label, value) in zip(risk_cols, risk_metrics):
            rcol.metric(label=label, value=value)

# Main Application
def main():
    st.sidebar.image("https://bin.bnbstatic.com/static/images/common/logo.png", width=200)
    st.sidebar.title("Navigation")
    
    menu_options = {
        "Open Positions": render_open_positions,
        "Open Trades": lambda: st.write("Open Trades Implementation"),  # Add similar implementation
        "Order History": lambda: st.write("Order History Implementation"),
        "Trade History": render_trade_history,
        "Position History": lambda: st.write("Position History Implementation"),
        "Advanced Analysis": render_analysis
    }
    
    selected = st.sidebar.radio("Menu", list(menu_options.keys()))
    menu_options[selected]()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        Binance Futures Dashboard • Real-time Analytics • 
        <a href="https://binance.com" target="_blank">Data Source</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
