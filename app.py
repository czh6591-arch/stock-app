import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Stock Analysis App", page_icon="📈", layout="wide")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Stock Price", "Compare Two Stocks", "Strategy Backtesting Lite"])

# Helper functions
@st.cache_data

def get_stock_data(ticker, start_date, end_date):
    """Get stock data from Yahoo Finance"""
    try:
        df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        return df
    except Exception as e:
        st.error(f"Error getting data for {ticker}: {e}")
        return None


def calculate_returns(df):
    """Calculate percentage returns"""
    df['Return%'] = df['Close'].pct_change() * 100
    return df


def normalize_data(df):
    """Normalize data to 100"""
    return (df / df.iloc[0]) * 100


def calculate_statistics(df, ticker):
    """Calculate key statistics for a stock"""
    if df.empty:
        return None
    
    # Calculate returns if not present
    if 'Return%' not in df.columns:
        df = calculate_returns(df)
    
    # Get the first and last closing prices
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    
    # Calculate total return
    total_return = ((last_close - first_close) / first_close) * 100
    
    # Calculate mean return and volatility
    mean_return = df['Return%'].mean()
    volatility = df['Return%'].std()
    
    # Calculate max drawdown
    df['CumulativeReturn'] = (1 + df['Return%'] / 100).cumprod()
    df['Peak'] = df['CumulativeReturn'].cummax()
    df['Drawdown'] = (df['CumulativeReturn'] - df['Peak']) / df['Peak'] * 100
    max_drawdown = df['Drawdown'].min()
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0)
    sharpe_ratio = mean_return / volatility * np.sqrt(252) if volatility != 0 else 0
    
    return {
        'Ticker': str(ticker),
        'Total Return (%)': round(total_return, 2),
        'Mean Return (%)': round(mean_return, 2),
        'Volatility (%)': round(volatility, 2),
        'Max Drawdown (%)': round(max_drawdown, 2),
        'Sharpe Ratio': round(sharpe_ratio, 2)
    }


def apply_moving_average_strategy(df, short_window=5, long_window=20):
    """Apply moving average crossover strategy"""
    if df.empty:
        return None
    
    # Create a copy of the DataFrame to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Calculate moving averages
    df['MA5'] = df['Close'].rolling(window=short_window).mean()
    df['MA20'] = df['Close'].rolling(window=long_window).mean()
    
    # Generate trading signals
    df['Signal'] = 0
    # Use .iloc for positional slicing
    df.iloc[short_window:, df.columns.get_loc('Signal')] = np.where(df['MA5'].iloc[short_window:] > df['MA20'].iloc[short_window:], 1, 0)
    
    # Generate trading orders
    df['Position'] = df['Signal'].diff()
    
    # Calculate returns
    df['Return%'] = df['Close'].pct_change() * 100
    
    # Calculate strategy returns
    df['StrategyReturn%'] = df['Return%'] * df['Signal'].shift(1)
    
    # Calculate cumulative returns
    df['CumulativeReturn'] = (1 + df['Return%'] / 100).cumprod()
    df['CumulativeStrategyReturn'] = (1 + df['StrategyReturn%'] / 100).cumprod()
    
    return df

# Stock Price page
if page == "Stock Price":
    st.title("Stock Price Analysis")
    
    # User input
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Enter stock ticker", "AAPL")
    with col2:
        start_date = st.date_input("Start date", datetime.today() - timedelta(days=365))
    with col3:
        end_date = st.date_input("End date", datetime.today())
    
    # Get stock data
    if ticker and start_date < end_date:
        df = get_stock_data(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            # Calculate returns
            df = calculate_returns(df)
            
            # Display data
            st.subheader(f"{ticker} Stock Data")
            st.dataframe(df.tail(10))
            
            # Plot price and volume
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{ticker} Close Price")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
                fig.update_layout(title=f"{ticker} Close Price", xaxis_title="Date", yaxis_title="Price")
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.subheader(f"{ticker} Volume")
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume'))
                fig.update_layout(title=f"{ticker} Volume", xaxis_title="Date", yaxis_title="Volume")
                st.plotly_chart(fig, width='stretch')
            
            # Plot returns
            st.subheader(f"{ticker} Daily Returns")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Return%'], name='Return%'))
            fig.update_layout(title=f"{ticker} Daily Returns", xaxis_title="Date", yaxis_title="Return%")
            # Add x-axis range slider for better navigation
            fig.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig, width='stretch')
            
            # Calculate and display statistics
            stats = calculate_statistics(df, ticker)
            if stats:
                st.subheader(f"{ticker} Key Statistics")
                # Display statistics directly without using DataFrame
                st.write(f"**Ticker:** {stats['Ticker']}")
                st.write(f"**Total Return (%):** {stats['Total Return (%)']}")
                st.write(f"**Mean Return (%):** {stats['Mean Return (%)']}")
                st.write(f"**Volatility (%):** {stats['Volatility (%)']}")
                st.write(f"**Max Drawdown (%):** {stats['Max Drawdown (%)']}")
                st.write(f"**Sharpe Ratio:** {stats['Sharpe Ratio']}")
        else:
            st.warning(f"No data found for {ticker}")
    else:
        st.warning("Please enter a valid ticker and date range")

# Compare Two Stocks page
elif page == "Compare Two Stocks":
    st.title("Compare Two Stocks")
    
    # User input
    col1, col2 = st.columns(2)
    with col1:
        ticker1 = st.text_input("Enter first stock ticker", "AAPL")
    with col2:
        ticker2 = st.text_input("Enter second stock ticker", "MSFT")
    
    col3, col4, col5 = st.columns(3)
    with col3:
        start_date = st.date_input("Start date", datetime.today() - timedelta(days=365))
    with col4:
        end_date = st.date_input("End date", datetime.today())
    with col5:
        compare_metric = st.selectbox("Compare metric", ["Close", "Volume", "Return%"])
    
    normalize = st.checkbox("Normalize to 100", value=False)
    
    # Get stock data
    if ticker1 and ticker2 and start_date < end_date:
        df1 = get_stock_data(ticker1, start_date, end_date)
        df2 = get_stock_data(ticker2, start_date, end_date)
        
        if df1 is not None and not df1.empty and df2 is not None and not df2.empty:
            # Calculate returns if needed
            if compare_metric == "Return%":
                df1 = calculate_returns(df1)
                df2 = calculate_returns(df2)
            
            # Normalize data if selected
            if normalize and compare_metric != "Return%":
                df1_normalized = normalize_data(df1[[compare_metric]])
                df2_normalized = normalize_data(df2[[compare_metric]])
                combined_df = pd.concat([df1_normalized, df2_normalized], axis=1)
                combined_df.columns = [f"{ticker1} {compare_metric}", f"{ticker2} {compare_metric}"]
            else:
                combined_df = pd.concat([df1[compare_metric], df2[compare_metric]], axis=1)
                combined_df.columns = [f"{ticker1} {compare_metric}", f"{ticker2} {compare_metric}"]
            
            # Plot comparison
            st.subheader(f"{ticker1} vs {ticker2} - {compare_metric}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=combined_df.index, y=combined_df.iloc[:, 0], name=ticker1))
            fig.add_trace(go.Scatter(x=combined_df.index, y=combined_df.iloc[:, 1], name=ticker2))
            fig.update_layout(title=f"{ticker1} vs {ticker2} - {compare_metric}", 
                              xaxis_title="Date", 
                              yaxis_title=f"{compare_metric}" + (" (Normalized)" if normalize else ""))
            st.plotly_chart(fig, width='stretch')
            
            # Plot volume comparison if selected
            if compare_metric != "Volume":
                st.subheader(f"{ticker1} vs {ticker2} - Volume")
                # Merge the two DataFrames on index to ensure alignment
                volume_df = pd.merge(df1[['Volume']], df2[['Volume']], left_index=True, right_index=True)
                volume_df.columns = [f"{ticker1} Volume", f"{ticker2} Volume"]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=volume_df.index, y=volume_df.iloc[:, 0], name=ticker1))
                fig.add_trace(go.Bar(x=volume_df.index, y=volume_df.iloc[:, 1], name=ticker2))
                fig.update_layout(title=f"{ticker1} vs {ticker2} - Volume", 
                                  xaxis_title="Date", 
                                  yaxis_title="Volume",
                                  barmode='group')
                # Add x-axis range slider for better navigation
                fig.update_xaxes(rangeslider_visible=True)
                st.plotly_chart(fig, width='stretch')
            
            # Calculate and display statistics
            stats1 = calculate_statistics(df1, ticker1)
            stats2 = calculate_statistics(df2, ticker2)
            
            if stats1 and stats2:
                st.subheader("Comparison Statistics")
                # Display statistics in a two-column layout
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{stats1['Ticker']} Statistics:**")
                    st.write(f"- Total Return (%): {stats1['Total Return (%)']}")
                    st.write(f"- Mean Return (%): {stats1['Mean Return (%)']}")
                    st.write(f"- Volatility (%): {stats1['Volatility (%)']}")
                    st.write(f"- Max Drawdown (%): {stats1['Max Drawdown (%)']}")
                    st.write(f"- Sharpe Ratio: {stats1['Sharpe Ratio']}")
                
                with col2:
                    st.write(f"**{stats2['Ticker']} Statistics:**")
                    st.write(f"- Total Return (%): {stats2['Total Return (%)']}")
                    st.write(f"- Mean Return (%): {stats2['Mean Return (%)']}")
                    st.write(f"- Volatility (%): {stats2['Volatility (%)']}")
                    st.write(f"- Max Drawdown (%): {stats2['Max Drawdown (%)']}")
                    st.write(f"- Sharpe Ratio: {stats2['Sharpe Ratio']}")
                
                # Calculate and display difference
                st.subheader("Difference (Ticker1 - Ticker2)")
                diff_stats = {
                    'Total Return (%)': round(stats1['Total Return (%)'] - stats2['Total Return (%)'], 2),
                    'Mean Return (%)': round(stats1['Mean Return (%)'] - stats2['Mean Return (%)'], 2),
                    'Volatility (%)': round(stats1['Volatility (%)'] - stats2['Volatility (%)'], 2),
                    'Max Drawdown (%)': round(stats1['Max Drawdown (%)'] - stats2['Max Drawdown (%)'], 2),
                    'Sharpe Ratio': round(stats1['Sharpe Ratio'] - stats2['Sharpe Ratio'], 2)
                }
                # Display difference statistics
                st.write(f"- Total Return Difference (%): {diff_stats['Total Return (%)']}")
                st.write(f"- Mean Return Difference (%): {diff_stats['Mean Return (%)']}")
                st.write(f"- Volatility Difference (%): {diff_stats['Volatility (%)']}")
                st.write(f"- Max Drawdown Difference (%): {diff_stats['Max Drawdown (%)']}")
                st.write(f"- Sharpe Ratio Difference: {diff_stats['Sharpe Ratio']}")
        else:
            st.warning(f"No data found for one or both tickers: {ticker1}, {ticker2}")
    else:
        st.warning("Please enter valid tickers and date range")

# Strategy Backtesting Lite page
elif page == "Strategy Backtesting Lite":
    st.title("Strategy Backtesting Lite")
    st.subheader("Moving Average Crossover Strategy")
    st.write("Strategy: Buy when MA5 > MA20, Sell when MA5 < MA20")
    
    # User input
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Enter stock ticker", "AAPL")
    with col2:
        start_date = st.date_input("Start date", datetime.today() - timedelta(days=365))
    with col3:
        end_date = st.date_input("End date", datetime.today())
    
    # Get stock data and apply strategy
    if ticker and start_date < end_date:
        df = get_stock_data(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            # Apply moving average strategy
            df = apply_moving_average_strategy(df)
            
            # Plot results
            st.subheader(f"{ticker} - Strategy Backtesting Results")
            
            # Create figure with price, MA5, MA20, and trading signals
            fig = go.Figure()
            
            # Add price and moving averages
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5', line=dict(width=2)))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(width=2)))
            
            # Add buy signals (green arrows)
            buy_signals = df[df['Position'] == 1]
            if not buy_signals.empty:
                fig.add_trace(go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['Close'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(symbol='triangle-up', size=12, color='green', line=dict(width=1, color='darkgreen'))
                ))
            
            # Add sell signals (red arrows)
            sell_signals = df[df['Position'] == -1]
            if not sell_signals.empty:
                fig.add_trace(go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['Close'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(symbol='triangle-down', size=12, color='red', line=dict(width=1, color='darkred'))
                ))
            
            # Update layout
            fig.update_layout(title=f"{ticker} - Moving Average Strategy",
                              xaxis_title="Date",
                              yaxis_title="Price",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            # Add x-axis range slider for better navigation
            fig.update_xaxes(rangeslider_visible=True)
            
            st.plotly_chart(fig, width='stretch')
            
            # Plot cumulative returns
            st.subheader(f"{ticker} - Cumulative Returns")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['CumulativeReturn'], name='Buy and Hold'))
            fig.add_trace(go.Scatter(x=df.index, y=df['CumulativeStrategyReturn'], name='Strategy'))
            fig.update_layout(title=f"{ticker} - Cumulative Returns",
                              xaxis_title="Date",
                              yaxis_title="Cumulative Return",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            # Add x-axis range slider for better navigation
            fig.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig, width='stretch')
            
            # Calculate and display strategy performance
            st.subheader("Strategy Performance")
            
            # Get final returns
            final_buy_hold = df['CumulativeReturn'].iloc[-1] * 100 - 100
            final_strategy = df['CumulativeStrategyReturn'].iloc[-1] * 100 - 100
            
            # Calculate number of trades
            num_buys = len(buy_signals)
            num_sells = len(sell_signals)
            num_trades = num_buys + num_sells
            
            # Calculate win rate (assuming each trade is a buy-sell pair)
            if num_buys > 0:
                # For simplicity, assume each buy has a corresponding sell
                # Calculate the return for each trade
                trade_returns = []
                for i in range(num_buys):
                    buy_date = buy_signals.index[i]
                    # Find the next sell date
                    sell_candidates = sell_signals[sell_signals.index > buy_date]
                    if not sell_candidates.empty:
                        sell_date = sell_candidates.index[0]
                        buy_price = float(df.loc[buy_date, 'Close'])
                        sell_price = float(df.loc[sell_date, 'Close'])
                        trade_return = ((sell_price - buy_price) / buy_price) * 100
                        trade_returns.append(trade_return)
                
                # Calculate win rate
                if trade_returns:
                    # Convert trade_returns to a list of floats
                    trade_returns = [float(r) for r in trade_returns]
                    num_winning_trades = len([r for r in trade_returns if r > 0])
                    win_rate = (num_winning_trades / len(trade_returns)) * 100
                else:
                    win_rate = 0
            else:
                win_rate = 0
            
            # Display performance statistics directly
            st.write(f"**Final Buy and Hold Return (%):** {round(final_buy_hold, 2)}")
            st.write(f"**Final Strategy Return (%):** {round(final_strategy, 2)}")
            st.write(f"**Strategy Outperformance (%):** {round(final_strategy - final_buy_hold, 2)}")
            st.write(f"**Number of Trades:** {num_trades}")
            st.write(f"**Number of Buy Signals:** {num_buys}")
            st.write(f"**Number of Sell Signals:** {num_sells}")
            st.write(f"**Win Rate (%):** {round(win_rate, 2)}")
            
            # Display trading signals
            st.subheader("Trading Signals")
            
            # Display buy signals
            if not buy_signals.empty:
                st.write("**Buy Signals:**")
                for date, price in buy_signals['Close'].items():
                    st.write(f"- {date.strftime('%Y-%m-%d')}: ${price:.2f}")
            
            # Display sell signals
            if not sell_signals.empty:
                st.write("**Sell Signals:**")
                for date, price in sell_signals['Close'].items():
                    st.write(f"- {date.strftime('%Y-%m-%d')}: ${price:.2f}")
        else:
            st.warning(f"No data found for {ticker}")
    else:
        st.warning("Please enter a valid ticker and date range")
