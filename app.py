import streamlit as st
import yfinance as yf
import pandas as pd
import cufflinks as cf
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Initialize cufflinks
cf.go_offline()

# App title
st.markdown('''
# Stock Price App
Shown are the stock price data for query companies!

**Credits**
- App built by [Chanin Nantasenamat](https://medium.com/@chanin.nantasenamat) (aka [Data Professor](http://youtube.com/dataprofessor))
- Built in `Python` using `streamlit`,`yfinance`, `cufflinks`, `pandas` and `datetime`
''')
st.write('---')

# Sidebar navigation
st.sidebar.title('Navigation')
page = st.sidebar.radio('Select a page:', ['Single Stock', 'Compare Two Stocks', 'Strategy Backtesting Lite'])

# Common functions
def get_ticker_info(ticker_symbol):
    return yf.Ticker(ticker_symbol)

@st.cache_data
def get_ticker_history(ticker_symbol, start_date, end_date):
    ticker_data = yf.Ticker(ticker_symbol)
    return ticker_data.history(start=start_date, end=end_date)

@st.cache_data
def get_ticker_list():
    return pd.read_csv('https://raw.githubusercontent.com/dataprofessor/s-and-p-500-companies/master/data/constituents_symbols.txt')

# Single Stock page
if page == 'Single Stock':
    # Sidebar
    st.sidebar.subheader('Query parameters')
    start_date = st.sidebar.date_input("Start date", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("End date", datetime.date(2021, 1, 31))

    # Retrieving tickers data
    ticker_list = get_ticker_list()
    tickerSymbol = st.sidebar.selectbox('Stock ticker', ticker_list) # Select ticker symbol
    tickerData = get_ticker_info(tickerSymbol)
    tickerDf = get_ticker_history(tickerSymbol, start_date, end_date)

    # Ticker information
    string_logo = '<img src=%s>' % tickerData.info['logo_url']
    st.markdown(string_logo, unsafe_allow_html=True)

    string_name = tickerData.info['longName']
    st.header('**%s**' % string_name)

    string_summary = tickerData.info['longBusinessSummary']
    st.info(string_summary)

    # Ticker data
    st.header('**Ticker data**')
    st.write(tickerDf)

    # Bollinger bands
    st.header('**Bollinger Bands**')
    qf=cf.QuantFig(tickerDf,title='First Quant Figure',legend='top',name='GS')
    qf.add_bollinger_bands()
    fig = qf.iplot(asFigure=True)
    st.plotly_chart(fig)

# Compare Two Stocks page
elif page == 'Compare Two Stocks':
    st.header('**Compare Two Stocks**')
    
    # Sidebar
    st.sidebar.subheader('Query parameters')
    start_date = st.sidebar.date_input("Start date", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("End date", datetime.date(2021, 1, 31))
    
    # Get ticker list
    ticker_list = get_ticker_list()
    
    # Select two tickers
    col1, col2 = st.sidebar.columns(2)
    with col1:
        ticker1 = st.selectbox('Stock 1', ticker_list, key='ticker1')
    with col2:
        ticker2 = st.selectbox('Stock 2', ticker_list, key='ticker2')
    
    # Select comparison metric
    metric = st.sidebar.selectbox('Comparison metric', ['Close', 'Volume', 'Return%'])
    
    # Normalize to 100 option
    normalize = st.sidebar.checkbox('Normalize to 100')
    
    # Get data for both tickers
    tickerData1 = get_ticker_info(ticker1)
    tickerDf1 = get_ticker_history(ticker1, start_date, end_date)
    tickerData2 = get_ticker_info(ticker2)
    tickerDf2 = get_ticker_history(ticker2, start_date, end_date)
    
    # Calculate returns if selected
    if metric == 'Return%':
        tickerDf1['Return%'] = tickerDf1['Close'].pct_change() * 100
        tickerDf2['Return%'] = tickerDf2['Close'].pct_change() * 100
    
    # Normalize data if selected
    if normalize:
        if metric in tickerDf1.columns:
            tickerDf1[metric] = (tickerDf1[metric] / tickerDf1[metric].iloc[0]) * 100
        if metric in tickerDf2.columns:
            tickerDf2[metric] = (tickerDf2[metric] / tickerDf2[metric].iloc[0]) * 100
    
    # Create comparison plot
    st.header(f'**{metric} Comparison: {ticker1} vs {ticker2}**')
    
    if metric == 'Volume':
        # Create bar chart for volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        fig.add_trace(
            go.Bar(x=tickerDf1.index, y=tickerDf1['Volume'], name=f'{ticker1} Volume', marker_color='blue'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=tickerDf2.index, y=tickerDf2['Volume'], name=f'{ticker2} Volume', marker_color='green'),
            row=2, col=1
        )
        
        fig.update_layout(
            title='Volume Comparison',
            xaxis_title='Date',
            yaxis_title='Volume',
            height=600
        )
        
    else:
        # Create line chart for Close or Return%
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(x=tickerDf1.index, y=tickerDf1[metric], name=f'{ticker1} {metric}', line=dict(color='blue'))
        )
        
        fig.add_trace(
            go.Scatter(x=tickerDf2.index, y=tickerDf2[metric], name=f'{ticker2} {metric}', line=dict(color='green'))
        )
        
        fig.update_layout(
            title=f'{metric} Comparison',
            xaxis_title='Date',
            yaxis_title=metric,
            height=600
        )
    
    st.plotly_chart(fig)
    
    # Create comparison table
    st.header('**Comparison Table**')
    
    # Calculate metrics
    metrics = ['Return%', 'Mean', 'Volatility']
    
    # For Close price
    if metric == 'Close':
        # Calculate returns for both stocks
        returns1 = tickerDf1['Close'].pct_change() * 100
        returns2 = tickerDf2['Close'].pct_change() * 100
        
        # Calculate final returns
        final_return1 = ((tickerDf1['Close'].iloc[-1] / tickerDf1['Close'].iloc[0]) - 1) * 100
        final_return2 = ((tickerDf2['Close'].iloc[-1] / tickerDf2['Close'].iloc[0]) - 1) * 100
        
        # Calculate mean returns
        mean1 = returns1.mean()
        mean2 = returns2.mean()
        
        # Calculate volatility (standard deviation of returns)
        volatility1 = returns1.std()
        volatility2 = returns2.std()
    
    # For Volume
    elif metric == 'Volume':
        # Calculate final returns (percentage change from first to last volume)
        final_return1 = ((tickerDf1['Volume'].iloc[-1] / tickerDf1['Volume'].iloc[0]) - 1) * 100
        final_return2 = ((tickerDf2['Volume'].iloc[-1] / tickerDf2['Volume'].iloc[0]) - 1) * 100
        
        # Calculate mean volume
        mean1 = tickerDf1['Volume'].mean()
        mean2 = tickerDf2['Volume'].mean()
        
        # Calculate volatility (standard deviation of volume)
        volatility1 = tickerDf1['Volume'].std()
        volatility2 = tickerDf2['Volume'].std()
    
    # For Return%
    else:
        # Calculate final returns (sum of daily returns)
        final_return1 = tickerDf1['Return%'].sum()
        final_return2 = tickerDf2['Return%'].sum()
        
        # Calculate mean returns
        mean1 = tickerDf1['Return%'].mean()
        mean2 = tickerDf2['Return%'].mean()
        
        # Calculate volatility (standard deviation of returns)
        volatility1 = tickerDf1['Return%'].std()
        volatility2 = tickerDf2['Return%'].std()
    
    # Create DataFrame for comparison table
    comparison_data = {
        'Metric': metrics,
        ticker1: [f'{final_return1:.2f}%', f'{mean1:.2f}', f'{volatility1:.2f}'],
        ticker2: [f'{final_return2:.2f}%', f'{mean2:.2f}', f'{volatility2:.2f}']
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.write(comparison_df)

# Strategy Backtesting Lite page
elif page == 'Strategy Backtesting Lite':
    st.header('**Strategy Backtesting Lite**')
    
    # Sidebar
    st.sidebar.subheader('Query parameters')
    start_date = st.sidebar.date_input("Start date", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("End date", datetime.date(2021, 1, 31))
    
    # Get ticker list
    ticker_list = get_ticker_list()
    
    # Select ticker
    tickerSymbol = st.sidebar.selectbox('Stock ticker', ticker_list)
    
    # Get ticker data
    tickerData = get_ticker_info(tickerSymbol)
    tickerDf = get_ticker_history(tickerSymbol, start_date, end_date)
    
    # Calculate moving averages
    tickerDf['MA5'] = tickerDf['Close'].rolling(window=5).mean()
    tickerDf['MA20'] = tickerDf['Close'].rolling(window=20).mean()
    
    # Generate trading signals
    tickerDf['Signal'] = 0
    tickerDf['Signal'][5:] = np.where(tickerDf['MA5'][5:] > tickerDf['MA20'][5:], 1, 0)
    
    # Calculate positions
    tickerDf['Position'] = tickerDf['Signal'].diff()
    
    # Calculate returns
    tickerDf['Return'] = tickerDf['Close'].pct_change()
    tickerDf['Strategy Return'] = tickerDf['Return'] * tickerDf['Signal'].shift(1)
    
    # Calculate cumulative returns
    tickerDf['Cumulative Market Return'] = (1 + tickerDf['Return']).cumprod()
    tickerDf['Cumulative Strategy Return'] = (1 + tickerDf['Strategy Return']).cumprod()
    
    # Create plot with trading signals
    st.header('**Trading Strategy: MA5 > MA20**')
    
    fig = go.Figure()
    
    # Add Close price
    fig.add_trace(
        go.Scatter(x=tickerDf.index, y=tickerDf['Close'], name='Close Price', line=dict(color='blue'))
    )
    
    # Add MA5
    fig.add_trace(
        go.Scatter(x=tickerDf.index, y=tickerDf['MA5'], name='MA5', line=dict(color='orange'))
    )
    
    # Add MA20
    fig.add_trace(
        go.Scatter(x=tickerDf.index, y=tickerDf['MA20'], name='MA20', line=dict(color='green'))
    )
    
    # Add buy signals (green arrows)
    buy_signals = tickerDf[tickerDf['Position'] == 1]
    fig.add_trace(
        go.Scatter(
            x=buy_signals.index, 
            y=buy_signals['Close'], 
            mode='markers', 
            name='Buy Signal', 
            marker=dict(color='green', symbol='arrow-up', size=12)
        )
    )
    
    # Add sell signals (red arrows)
    sell_signals = tickerDf[tickerDf['Position'] == -1]
    fig.add_trace(
        go.Scatter(
            x=sell_signals.index, 
            y=sell_signals['Close'], 
            mode='markers', 
            name='Sell Signal', 
            marker=dict(color='red', symbol='arrow-down', size=12)
        )
    )
    
    fig.update_layout(
        title=f'{tickerSymbol} - MA5 vs MA20 Strategy',
        xaxis_title='Date',
        yaxis_title='Price',
        height=600
    )
    
    st.plotly_chart(fig)
    
    # Create cumulative returns plot
    st.header('**Cumulative Returns**')
    
    fig_returns = go.Figure()
    
    fig_returns.add_trace(
        go.Scatter(x=tickerDf.index, y=tickerDf['Cumulative Market Return'], name='Market Return', line=dict(color='blue'))
    )
    
    fig_returns.add_trace(
        go.Scatter(x=tickerDf.index, y=tickerDf['Cumulative Strategy Return'], name='Strategy Return', line=dict(color='green'))
    )
    
    fig_returns.update_layout(
        title='Cumulative Returns: Market vs Strategy',
        xaxis_title='Date',
        yaxis_title='Cumulative Return',
        height=600
    )
    
    st.plotly_chart(fig_returns)
    
    # Create final returns table
    st.header('**Final Returns**')
    
    # Calculate final returns
    final_market_return = (tickerDf['Cumulative Market Return'].iloc[-1] - 1) * 100
    final_strategy_return = (tickerDf['Cumulative Strategy Return'].iloc[-1] - 1) * 100
    
    # Calculate number of trades
    num_buy_signals = len(buy_signals)
    num_sell_signals = len(sell_signals)
    num_trades = min(num_buy_signals, num_sell_signals)
    
    # Create DataFrame for final returns
    returns_data = {
        'Metric': ['Final Market Return', 'Final Strategy Return', 'Number of Trades'],
        'Value': [f'{final_market_return:.2f}%', f'{final_strategy_return:.2f}%', num_trades]
    }
    
    returns_df = pd.DataFrame(returns_data)
    st.write(returns_df)