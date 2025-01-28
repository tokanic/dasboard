import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
from datetime import datetime
import pytz

# Set page configuration
st.set_page_config(page_title="🚀 Enhanced Binance Trading Dashboard", layout="wide")

# Apply custom CSS for styling and animations
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom right, #141e30, #243b55);
        color: white;
    }
    [data-testid="stSidebar"] {
        background: #141e30;
        color: white;
    }
    .flashcard {
        background: linear-gradient(to bottom right, #ff7e5f, #feb47b);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Utility Functions
def format_timestamp(timestamp):
    """Convert timestamp to Indian Standard Time."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
        indian_tz = pytz.timezone('Asia/Kolkata')
        indian_time = dt.astimezone(indian_tz)
        return indian_time.strftime('%d %b %Y %I:%M:%S %p')
    except Exception as e:
        return f"Invalid Time ({e})"

def fetch_data(endpoint):
    """Fetch data from API with error handling."""
    try:
        response = requests.get(f"{API_SERVER}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return None

# Reusable Components
def display_dataframe_with_search(df, title):
    """Display a searchable dataframe."""
    st.subheader(title + " 🔎")
    search_term = st.text_input(f"Search {title}:", "").lower()
    if not df.empty:
        if search_term:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        st.dataframe(df.style.background_gradient(cmap='coolwarm'), use_container_width=True)
    else:
        st.warning(f"No data available for {title}.")

def display_flashcard(title, value, emoji):
    """Display a single flashcard."""
    st.markdown(f"""
    <div class="flashcard">
        {emoji} {title}: <br><span style="font-size: 24px;">{value}</span>
    </div>
    """, unsafe_allow_html=True)

def display_trend_graph(df, x_col, y_col, title):
    """Create a trend graph."""
    if x_col in df.columns and y_col in df.columns:
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"Missing columns for trend graph: {x_col}, {y_col}")

# Flask API Server URL
API_SERVER = "http://34.47.211.154:5000"  # Replace with your AWS server IP

# Utility Functions
def format_timestamp(timestamp):
    """Convert timestamp to Indian Standard Time"""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
        indian_tz = pytz.timezone('Asia/Kolkata')
        indian_time = dt.astimezone(indian_tz)
        return indian_time.strftime('%d %b %Y %I:%M:%S %p')
    except Exception as e:
        return f"Invalid Time ({e})"

def format_pnl(pnl):
    """Format PNL with color coding"""
    try:
        pnl = float(pnl)
        if pnl > 0:
            return f'<span style="color:green">+{pnl:.2f} USDT</span>'
        elif pnl < 0:
            return f'<span style="color:red">{pnl:.2f} USDT</span>'
        else:
            return f'{pnl:.2f} USDT'
    except Exception as e:
        return f"N/A ({e})"

def fetch_data(endpoint):
    """Fetch data from API with error handling"""
    try:
        response = requests.get(f"{API_SERVER}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return None


def traders_with_open_positions():
    """Display Open Positions by Traders"""
    st.subheader("Traders with Open Positions")
    open_positions_data = fetch_data("open_positions")  # Replace with the correct API endpoint for open positions
    
    if open_positions_data:
        df = pd.DataFrame(open_positions_data)
        if not df.empty:
            # Display Open Positions grouped by Trader
            st.dataframe(df, use_container_width=True)
            # Visualization: Group positions by Trader
            grouped_data = df.groupby('Trader')['Size'].sum().reset_index()
            fig = px.bar(
                grouped_data,
                x='Trader',
                y='Size',
                title='Open Positions Size by Trader',
                labels={'Trader': 'Trader', 'Size': 'Position Size (USDT)'},
                text='Size'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No open positions found.")
    else:
        st.error("Failed to fetch open positions data.")


def order_history():
    """Display Order History."""
    st.subheader("📜 Order History")
    order_history_data = fetch_data("order_history")
    if order_history_data:
        df = pd.DataFrame(order_history_data)
        if not df.empty:
            display_dataframe_with_search(df, "Order History")
        else:
            st.warning("No order history found.")
    else:
        st.error("Failed to fetch order history data.")



def trade_history():
    """Display Trade History."""
    st.subheader("📊 Trade History")
    trade_history_data = fetch_data("trade_history")
    if trade_history_data:
        df = pd.DataFrame(trade_history_data)
        if not df.empty:
            display_dataframe_with_search(df, "Trade History")
            display_trend_graph(df, "Time", "PNL", "Trade History PNL Over Time")
        else:
            st.warning("No trade history found.")
    else:
        st.error("Failed to fetch trade history data.")

def closed_positions_cost_analysis():
    """Display Closed Positions Cost Analysis"""
    st.subheader("Closed Positions Analysis")
    closed_positions_data = fetch_data("closed_positions")  # Replace with the correct API endpoint for closed positions
    
    if closed_positions_data:
        df = pd.DataFrame(closed_positions_data)
        if not df.empty:
            # Sort by Exit Time, latest first
            df.sort_values(by='Exit Time', ascending=False, inplace=True)
            
            # Highlight Positions with Loss
            df['Profit/Loss'] = df['PNL'].apply(lambda x: "Loss" if float(x) < 0 else "Profit")
            st.dataframe(df, use_container_width=True)

            # Visualization: Loss vs Profit
            fig = px.pie(
                df,
                names='Profit/Loss',
                title='Profit vs Loss in Closed Positions',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No closed positions data found.")
    else:
        st.error("Failed to fetch closed positions data.")

# Dashboard Sections
def account_summary():
    """Comprehensive Account Summary"""
    st.subheader("Account Summary")
    account_summary = fetch_data("account_summary")
    
    if account_summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Total Balance", value=f"{account_summary['Balance']:.2f} USDT")
        
        with col2:
            st.metric(label="Unrealized PNL", value=account_summary['Unrealized PNL'])
        
        with col3:
            st.metric(label="Margin Balance", value=f"{account_summary['Margin Balance']:.2f} USDT")
        
        with col4:
            st.metric(label="Available Balance", value=f"{account_summary['Available Balance']:.2f} USDT")

def positions():
    """Advanced Positions Analysis"""
    st.subheader("Active Positions")
    positions_data = fetch_data("positions")
    
    if positions_data:
        df = pd.DataFrame(positions_data)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Position Distribution Chart
            fig = px.pie(df, names='Symbol', values='Size', title='Position Size Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No active positions found.")

def open_orders():
    """Open Orders Analysis with Enhanced Visualization"""
    st.subheader("Open Orders")
    open_orders_data = fetch_data("open_orders")  # Ensure correct API endpoint
    
    if open_orders_data:
        df = pd.DataFrame(open_orders_data)

        # Print the available columns for debugging
        st.write("Columns in Open Orders Data:", df.columns.tolist())

        if not df.empty:
            # Check if 'Order Time' exists before processing
            if 'Order Time' in df.columns:
                df['Order Time'] = pd.to_datetime(df['Order Time'], unit='ms', errors='coerce')
                df['Order Time'] = df['Order Time'].dt.strftime('%d %b %Y %I:%M:%S %p')
                df.sort_values(by='Order Time', ascending=False, inplace=True)
            else:
                st.warning("'Order Time' column is missing from the API response.")

            # Display DataFrame
            st.dataframe(df, use_container_width=True, height=500)

            # Order Status Distribution Pie Chart
            if 'Status' in df.columns:
                status_fig = px.pie(
                    df,
                    names='Status',
                    title='Order Status Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(status_fig, use_container_width=True)

            # Order Type Distribution Bar Chart
            if 'Type' in df.columns:
                type_fig = px.bar(
                    df,
                    x=df['Type'].value_counts().index,
                    y=df['Type'].value_counts().values,
                    title='Order Type Distribution',
                    labels={'x': 'Order Type', 'y': 'Count'},
                    text_auto=True
                )
                st.plotly_chart(type_fig, use_container_width=True)

        else:
            st.warning("No open orders found.")
    else:
        st.warning("Failed to fetch open orders.")


def position_history():
    """Display Position History with Improved Formatting"""
    st.subheader("Position History")
    position_history_data = fetch_data("position_history")  # Ensure correct API endpoint

    if position_history_data:
        df = pd.DataFrame(position_history_data)
        if not df.empty:
            # Convert timestamps to a readable format
            if 'Entry Time' in df.columns:
                df['Entry Time'] = pd.to_datetime(df['Entry Time'], unit='ms', errors='coerce')
                df['Entry Time'] = df['Entry Time'].dt.strftime('%d %b %Y %I:%M:%S %p')

            if 'Exit Time' in df.columns:
                df['Exit Time'] = pd.to_datetime(df['Exit Time'], unit='ms', errors='coerce')
                df['Exit Time'] = df['Exit Time'].dt.strftime('%d %b %Y %I:%M:%S %p')

            # Convert PNL to float and format properly
            if 'PNL' in df.columns:
                df['PNL'] = pd.to_numeric(df['PNL'], errors='coerce')
                df['PNL'] = df['PNL'].apply(lambda x: f"+{x:.2f} USDT" if x > 0 else f"{x:.2f} USDT")

            # Sort by latest exit time first
            if 'Exit Time' in df.columns:
                df.sort_values(by='Exit Time', ascending=False, inplace=True)

            # Display DataFrame
            st.dataframe(df, use_container_width=True, height=500)

            # PNL Distribution Chart
            if 'PNL' in df.columns:
                df['PNL'] = df['PNL'].str.replace(" USDT", "").astype(float)  # Remove text for plotting
                fig = px.histogram(
                    df,
                    x='PNL',
                    title='Position PNL Distribution',
                    labels={'PNL': 'Profit/Loss (USDT)'},
                    color_discrete_sequence=['#EF553B']
                )
                st.plotly_chart(fig, use_container_width=True)

            # Entry vs Exit Price Scatter Plot
            if 'Entry Price' in df.columns and 'Exit Price' in df.columns:
                scatter_fig = px.scatter(
                    df,
                    x='Entry Price',
                    y='Exit Price',
                    color='Symbol',
                    size='PNL',
                    hover_data=['Entry Time', 'Exit Time'],
                    title='Entry vs Exit Price by Symbol',
                    labels={'Entry Price': 'Entry Price (USDT)', 'Exit Price': 'Exit Price (USDT)'}
                )
                st.plotly_chart(scatter_fig, use_container_width=True)

        else:
            st.warning("No position history available.")
    else:
        st.warning("Failed to fetch position history.")


def analytics():
    """Trading Analytics"""
    st.subheader("Trading Analytics")
    pnl_data = fetch_data("pnl_analytics")
    positions_data = fetch_data("positions")

    if pnl_data:
        pnl_df = pd.DataFrame(pnl_data)
        if not pnl_df.empty:
            # Sort by Date, latest first
            pnl_df['Date'] = pd.to_datetime(pnl_df['Date'])  # Ensure correct datetime format
            pnl_df.sort_values(by='Date', ascending=False, inplace=True)

            # Daily PNL Chart
            daily_fig = px.bar(
                pnl_df,
                x='Date',
                y='PNL',
                title='Daily Profit/Loss (PNL)',
                labels={'Date': 'Date', 'PNL': 'Profit/Loss (USDT)'},
                color='PNL',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            daily_fig.update_layout(xaxis_title='Date', yaxis_title='Profit/Loss (USDT)', xaxis=dict(tickformat='%b %d'))
            st.plotly_chart(daily_fig, use_container_width=True)

            # Cumulative PNL Chart
            pnl_df['Cumulative PNL'] = pnl_df['PNL'].cumsum()
            cumulative_fig = px.line(
                pnl_df,
                x='Date',
                y='Cumulative PNL',
                title='Cumulative Profit/Loss Over Time',
                labels={'Date': 'Date', 'Cumulative PNL': 'Cumulative Profit/Loss (USDT)'},
                line_shape='linear',
                markers=True
            )
            cumulative_fig.update_layout(xaxis_title='Date', yaxis_title='Cumulative Profit/Loss (USDT)', xaxis=dict(tickformat='%b %d'))
            st.plotly_chart(cumulative_fig, use_container_width=True)

    if positions_data:
        positions_df = pd.DataFrame(positions_data)
        if not positions_df.empty:
            # Pie Chart: Current Holdings
            pie_fig = px.pie(
                positions_df,
                names='Symbol',
                values='Size',
                title='Current Holdings Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(pie_fig, use_container_width=True)

            # Line Chart: Symbol-Wise Profit
            if 'PNL' in positions_df.columns and 'Symbol' in positions_df.columns:
                positions_df['PNL'] = positions_df['PNL'].astype(float)
                profit_line_fig = px.line(
                    positions_df,
                    x='Symbol',
                    y='PNL',
                    title='Profit by Symbol',
                    labels={'Symbol': 'Crypto Symbol', 'PNL': 'Profit/Loss (USDT)'},
                    markers=True,
                    line_shape='linear'
                )
                profit_line_fig.update_layout(xaxis_title='Crypto Symbol', yaxis_title='Profit/Loss (USDT)')
                st.plotly_chart(profit_line_fig, use_container_width=True)

    if not pnl_data and not positions_data:
        st.error("Failed to fetch analytics data. Please check the backend.")

# def trade_history():
#     """Comprehensive Trade History"""
#     st.subheader("Trade History")
#     trade_history_data = fetch_data("trade_history")

#     if trade_history_data:
#         df = pd.DataFrame(trade_history_data)
#         if not df.empty:
#             # Convert timestamp to human-readable format if 'Time' column exists
#             if 'Time' in df.columns:
#                 df['Time'] = pd.to_datetime(df['Time'], unit='ms', errors='coerce')
#                 df['Time'] = df['Time'].dt.strftime(" %d %b %Y %I:%M:%S %p")  # Format properly

#             # Format PNL for better readability (Remove HTML tags)
#             if 'PNL' in df.columns:
#                 df['PNL'] = df['PNL'].astype(float)
#                 df['PNL'] = df['PNL'].map(lambda x: f"+{x:.2f} USDT" if x > 0 else f"{x:.2f} USDT")

#             # Sort by time, latest first
#             df.sort_values(by='Time', ascending=False, inplace=True)

#             # Display DataFrame
#             st.dataframe(df, use_container_width=True, height=500)

#             # PNL Distribution Visualization
#             if 'PNL' in df.columns:
#                 fig = px.histogram(
#                     df, 
#                     x='PNL', 
#                     title='PNL Distribution', 
#                     labels={'PNL': 'Profit/Loss (USDT)'},
#                     color_discrete_sequence=['#636EFA']
#                 )
#                 st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("No trade history available.")
#     else:
#         st.warning("Failed to fetch trade history.")


def closed_positions():
    """Display Closed Positions"""
    st.subheader("Closed Positions")
    closed_positions_data = fetch_data("closed_positions")

    if closed_positions_data:
        df = pd.DataFrame(closed_positions_data)
        if not df.empty:
            # Sort by Exit Time, latest first
            df.sort_values(by='Exit Time', ascending=False, inplace=True)

            # Convert timestamps to human-readable format
            if 'Entry Time' in df.columns:
                df['Entry Time'] = df['Entry Time'].apply(format_timestamp)
            if 'Exit Time' in df.columns:
                df['Exit Time'] = df['Exit Time'].apply(format_timestamp)

            # Format PNL with color coding
            if 'PNL' in df.columns:
                df['PNL'] = df['PNL'].apply(format_pnl)

            # Display DataFrame
            st.dataframe(df, use_container_width=True, height=500)

            # PNL Distribution Chart
            if 'PNL' in df.columns:
                fig = px.histogram(
                    df, 
                    x='PNL', 
                    title='Closed Positions PNL Distribution', 
                    labels={'PNL': 'Profit/Loss (USDT)'},
                    color_discrete_sequence=['#EF553B']
                )
                st.plotly_chart(fig, use_container_width=True)

            # Entry vs Exit Price Scatter Plot
            if 'Entry Price' in df.columns and 'Exit Price' in df.columns:
                scatter_fig = px.scatter(
                    df,
                    x='Entry Price',
                    y='Exit Price',
                    color='Symbol',
                    size='PNL',
                    hover_data=['Entry Time', 'Exit Time'],
                    title='Entry vs Exit Price by Symbol',
                    labels={'Entry Price': 'Entry Price (USDT)', 'Exit Price': 'Exit Price (USDT)'}
                )
                st.plotly_chart(scatter_fig, use_container_width=True)
        else:
            st.warning("No closed positions available.")
    else:
        st.warning("Failed to fetch closed positions.")

def order_history():
    """Display Order History"""
    st.subheader("Order History")
    try:
        order_history_data = fetch_data("order_history")
        if order_history_data:
            df = pd.DataFrame(order_history_data)
            if not df.empty:
                # Sort by Order Time, latest first
                df.sort_values(by='Order Time', ascending=False, inplace=True)

                # Convert timestamps to human-readable format
                if 'Order Time' in df.columns:
                    df['Order Time'] = df['Order Time'].apply(format_timestamp)

                # Display DataFrame
                st.dataframe(df, use_container_width=True, height=500)

                # Order Status Distribution Pie Chart
                if 'Status' in df.columns:
                    status_fig = px.pie(
                        df,
                        names='Status',
                        title='Order Status Distribution',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(status_fig, use_container_width=True)

                # Order Type Distribution Bar Chart
                if 'Type' in df.columns:
                    type_fig = px.bar(
                        df,
                        x='Type',
                        title='Order Type Distribution',
                        labels={'Type': 'Order Type', 'count': 'Count'},
                        color_discrete_sequence=['#636EFA']
                    )
                    st.plotly_chart(type_fig, use_container_width=True)
            else:
                st.warning("No order history found.")
        else:
            st.error("No data received from the backend. Please ensure the `/order_history` endpoint is correctly configured.")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Main Dashboard
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/4b/Binance_logo.png", width=200)
    st.sidebar.title("Binance Trading Dashboard")
    
    # Navigation
    menu = [
        "Account Summary", 
        "Positions", 
        "Open Orders", 
        "Trade History", 
        "Position History",
        "Analytics",
        "Traders with Open Positions",  # New Page
        "Closed Positions Analysis"    # New Page
    ]
    choice = st.sidebar.radio("Navigation", menu)
    
    # Routing
    if choice == "Account Summary":
        account_summary()
    elif choice == "Positions":
        positions()
    elif choice == "Open Orders":
        open_orders()
    elif choice == "Trade History":
        trade_history()
    elif choice == "Position History":
        position_history()
    elif choice == "Analytics":
        analytics()
    elif choice == "Traders with Open Positions":
        traders_with_open_positions()  # Call the new function
    elif choice == "Closed Positions Analysis":
        closed_positions_cost_analysis()  # Call the new function
    st.markdown("---")
    st.text("© 2025 Binance Trading Dashboard")

if __name__ == "__main__":
    main()