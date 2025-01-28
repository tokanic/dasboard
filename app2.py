import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
from datetime import datetime
import pytz
import os
from functools import lru_cache

# Configuration
st.set_page_config(
    page_title="Binance Trading Dashboard",
    layout="wide",
    page_icon="📊"
)

# Constants
API_SERVER = "http://34.47.211.154:5000"  # GCP Flask API Server
TIMEZONE = pytz.timezone('Asia/Kolkata')
CACHE_TTL = 300  # 5 minutes cache

# Utility Functions
@st.cache_data(ttl=CACHE_TTL)
def fetch_data(endpoint):
    """Fetch data from API with enhanced error handling and caching"""
    try:
        response = requests.get(f"{API_SERVER}/{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {endpoint}: {str(e)}")
        return None

def format_datetime(timestamp):
    """Convert timestamp to formatted datetime string"""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
        return dt.astimezone(TIMEZONE).strftime('%d %b %Y %I:%M:%S %p')
    except (TypeError, ValueError):
        return "N/A"

def style_dataframe(df):
    """Apply consistent styling to dataframes"""
    return df.style.format(precision=2).background_gradient(
        cmap='Blues', subset=pd.IndexSlice[:, df.select_dtypes(include='number').columns]
    )

# Dashboard Components
def account_summary():
    """Enhanced Account Summary with Metrics"""
    st.subheader("📈 Account Overview")
    data = fetch_data("account_summary")
    
    if data:
        cols = st.columns(4)
        metrics = [
            ("Total Balance", f"{data['Balance']:,.2f} USDT", "#4CAF50"),
            ("Unrealized PNL", f"{float(data['Unrealized PNL']):+,.2f} USDT", "#FF6D00"),
            ("Margin Balance", f"{data['Margin Balance']:,.2f} USDT", "#2196F3"),
            ("Available Balance", f"{data['Available Balance']:,.2f} USDT", "#9C27B0")
        ]
        
        for col, (label, value, color) in zip(cols, metrics):
            col.markdown(
                f"<div style='padding:20px; background-color:{color}20; border-radius:10px;'>"
                f"<h3 style='color:{color}; margin:0;'>{label}</h3>"
                f"<h2 style='margin:0;'>{value}</h2></div>",
                unsafe_allow_html=True
            )

def positions_analysis():
    """Interactive Positions Analysis"""
    st.subheader("📊 Active Positions Analysis")
    data = fetch_data("positions")
    
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        if not df.empty:
            with st.expander("Detailed Positions", expanded=True):
                st.dataframe(
                    style_dataframe(df),
                    use_container_width=True,
                    height=400
                )
            
            cols = st.columns([2, 1])
            with cols[0]:
                fig = px.bar(
                    df,
                    x='Symbol',
                    y='Size',
                    color='PNL',
                    title='Position Size vs PNL',
                    color_continuous_scale='tealrose'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with cols[1]:
                fig = px.pie(
                    df,
                    names='Symbol',
                    values='Size',
                    title='Position Distribution',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No active positions found")

def enhanced_open_orders():
    """Open Orders with Interactive Filters"""
    st.subheader("📨 Order Management")
    data = fetch_data("open_orders")
    
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        if not df.empty:
            # Add datetime conversion
            if 'time' in df.columns:
                df['Order Time'] = pd.to_datetime(df['time'], unit='ms').dt.tz_localize(TIMEZONE)
            
            # Interactive filters
            col1, col2 = st.columns(2)
            with col1:
                selected_symbol = st.selectbox(
                    "Filter by Symbol",
                    ['All'] + sorted(df['Symbol'].unique())
                )
            
            with col2:
                selected_type = st.multiselect(
                    "Filter by Order Type",
                    options=df['Type'].unique(),
                    default=df['Type'].unique()
                )
            
            # Apply filters
            filtered_df = df.copy()
            if selected_symbol != 'All':
                filtered_df = filtered_df[filtered_df['Symbol'] == selected_symbol]
            filtered_df = filtered_df[filtered_df['Type'].isin(selected_type)]
            
            # Display filtered results
            st.dataframe(
                style_dataframe(filtered_df),
                use_container_width=True,
                height=400
            )
            
            # Visualizations
            tabs = st.tabs(["Type Distribution", "Status Overview"])
            with tabs[0]:
                fig = px.histogram(
                    filtered_df,
                    x='Type',
                    color='Side',
                    title='Order Type Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tabs[1]:
                fig = px.sunburst(
                    filtered_df,
                    path=['Status', 'Type'],
                    title='Order Status Hierarchy'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No open orders found")

def performance_analytics():
    """Advanced Trading Performance Analytics"""
    st.subheader("📈 Performance Analytics")
    
    # PNL Analysis
    with st.spinner("Loading PNL Data..."):
        pnl_data = fetch_data("pnl_analytics")
    
    if pnl_data and isinstance(pnl_data, list):
        pnl_df = pd.DataFrame(pnl_data)
        pnl_df['Date'] = pd.to_datetime(pnl_df['Date'])
        pnl_df = pnl_df.sort_values('Date')
        
        # Cumulative PNL calculation
        pnl_df['Cumulative PNL'] = pnl_df['PNL'].cumsum()
        
        # Main chart
        fig = px.area(
            pnl_df,
            x='Date',
            y='Cumulative PNL',
            title='Cumulative PNL Over Time',
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics
        cols = st.columns(3)
        metrics = [
            ("Total Profit", pnl_df[pnl_df['PNL'] > 0]['PNL'].sum()),
            ("Total Loss", pnl_df[pnl_df['PNL'] < 0]['PNL'].sum()),
            ("Win Rate", len(pnl_df[pnl_df['PNL'] > 0])/len(pnl_df) if len(pnl_df) > 0 else 0)
        ]
        
        for col, (label, value) in zip(cols, metrics):
            col.metric(
                label=label,
                value=f"{value:+,.2f} USDT" if label != "Win Rate" else f"{value:.1%}"
            )

# Main Dashboard Layout
def main():
    # Sidebar Configuration
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/4b/Binance_logo.png", width=200)
    st.sidebar.title("Navigation")
    
    # Menu Options
    menu_options = {
        "Account Summary": account_summary,
        "Positions Analysis": positions_analysis,
        "Order Management": enhanced_open_orders,
        "Performance Analytics": performance_analytics
    }
    
    # Navigation Selection
    selected = st.sidebar.radio("Go to", list(menu_options.keys()))
    
    # Display selected page
    menu_options[selected]()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        Binance Trading Dashboard • Real-time Analytics • 
        <a href="https://binance.com" target="_blank">Data Source</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
