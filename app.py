import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 设置页面配置
st.set_page_config(page_title="Stock Analysis App", layout="wide")

# 侧边栏导航
page = st.sidebar.selectbox("Choose a page", ["Single Stock View", "Compare Two Stocks", "Strategy Backtesting Lite"])

if page == "Single Stock View":
    st.write("""
    # Simple Stock Price App

    Shown are the stock closing price and volume!

    """)

    # 用户输入ticker
    tickerSymbol = st.text_input('Enter Stock Ticker', 'GOOGL')
    # 获取日期范围
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input('Start Date', datetime(2010, 5, 31))
    with col2:
        end_date = st.date_input('End Date', datetime(2020, 5, 31))

    # 获取股票数据
    tickerData = yf.Ticker(tickerSymbol)
    tickerDf = tickerData.history(start=start_date, end=end_date)

    st.subheader(f"Closing Price of {tickerSymbol}")
    st.line_chart(tickerDf.Close)
    st.subheader(f"Volume of {tickerSymbol}")
    st.line_chart(tickerDf.Volume)

elif page == "Compare Two Stocks":
    st.title("Compare Two Stocks")
    
    # 获取用户输入
    col1, col2 = st.columns(2)
    with col1:
        ticker1 = st.text_input('First Stock Ticker', 'AAPL')
    with col2:
        ticker2 = st.text_input('Second Stock Ticker', 'MSFT')
    
    # 日期范围
    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input('Comparison Start Date', datetime(2020, 1, 1))
    with col4:
        end_date = st.date_input('Comparison End Date', datetime.today())
    
    # 对比指标和归一化选项
    metric = st.selectbox('Select Metric to Compare', ['Close', 'Volume', 'Return%'])
    normalize = st.checkbox('Normalize to 100', value=True)
    
    # 获取两个股票数据
    @st.cache_data
    def get_stock_data(ticker, start, end):
        data = yf.Ticker(ticker).history(start=start, end=end)
        data['Return%'] = data['Close'].pct_change() * 100
        return data
    
    data1 = get_stock_data(ticker1, start_date, end_date)
    data2 = get_stock_data(ticker2, start_date, end_date)
    
    # 处理归一化
    if normalize and metric != 'Volume' and metric != 'Return%':
        data1[metric] = (data1[metric] / data1[metric].iloc[0]) * 100
        data2[metric] = (data2[metric] / data2[metric].iloc[0]) * 100
    
    # 可视化
    st.subheader(f"{metric} Comparison: {ticker1} vs {ticker2}")
    compare_df = pd.DataFrame({
        f"{ticker1} {metric}": data1[metric],
        f"{ticker2} {metric}": data2[metric]
    })
    
    if metric == 'Volume':
        st.bar_chart(compare_df)
    else:
        st.line_chart(compare_df)
    
    # 对比表格
    st.subheader("Stock Comparison Metrics")
    metrics_df = pd.DataFrame({
        'Metric': ['Start Price', 'End Price', 'Total Return%', 'Avg Daily Return%', 'Volatility (Std Dev)'],
        ticker1: [
            round(data1['Close'].iloc[0], 2),
            round(data1['Close'].iloc[-1], 2),
            round(((data1['Close'].iloc[-1] / data1['Close'].iloc[0]) -1)*100, 2),
            round(data1['Return%'].mean(), 4),
            round(data1['Return%'].std(), 4)
        ],
        ticker2: [
            round(data2['Close'].iloc[0], 2),
            round(data2['Close'].iloc[-1], 2),
            round(((data2['Close'].iloc[-1] / data2['Close'].iloc[0]) -1)*100, 2),
            round(data2['Return%'].mean(), 4),
            round(data2['Return%'].std(), 4)
        ]
    })
    st.dataframe(metrics_df)

elif page == "Strategy Backtesting Lite":
    st.title("Moving Average Crossover Strategy Backtesting")
    
    # 用户输入
    ticker = st.text_input('Stock Ticker for Backtest', 'AAPL')
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input('Backtest Start Date', datetime(2020, 1, 1))
    with col2:
        end_date = st.date_input('Backtest End Date', datetime.today())
    
    # 获取股票数据并计算均线
    @st.cache_data
    def get_backtest_data(ticker, start, end):
        data = yf.Ticker(ticker).history(start=start, end=end)
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['Return%'] = data['Close'].pct_change()
        return data
    
    data = get_backtest_data(ticker, start_date, end_date)
    
    # 生成交易信号：MA5上穿MA20买入，下穿卖出
    data['Signal'] = 0
    # 当MA5从下向上穿过MA20时，生成买入信号
    data['Signal'] = np.where(data['MA5'] > data['MA20'], 1, 0)
    # 计算持仓变化
    data['Position'] = data['Signal'].diff()
    
    # 计算策略收益
    data['Strategy Return'] = data['Return%'] * data['Signal'].shift(1)
    data['Cumulative Buy&Hold'] = (1 + data['Return%']).cumprod() * 100
    data['Cumulative Strategy'] = (1 + data['Strategy Return']).cumprod() * 100
    
    # 可视化持仓曲线
    st.subheader(f"Strategy Performance for {ticker}")
    performance_df = pd.DataFrame({
        'Buy & Hold': data['Cumulative Buy&Hold'],
        'MA Crossover Strategy': data['Cumulative Strategy']
    })
    st.line_chart(performance_df)
    
    # 使用Plotly创建带交易信号的价格图表
    st.subheader("Price Chart with Trade Signals")
    fig = go.Figure()
    
    # 添加收盘价
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price', line=dict(color='#1f77b4')))
    # 添加MA5均线
    fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], name='MA5', line=dict(color='#2ca02c', dash='dot')))
    # 添加MA20均线
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name='MA20', line=dict(color='#ff7f0e', dash='dot')))
    
    # 添加买入信号（绿色向上箭头）
    buy_signals = data[data['Position'] == 1]
    fig.add_trace(go.Scatter(
        x=buy_signals.index, 
        y=buy_signals['Close'] * 0.98,
        name='Buy Signal',
        mode='markers',
        marker=dict(color='green', size=12, symbol='triangle-up')
    ))
    
    # 添加卖出信号（红色向下箭头）
    sell_signals = data[data['Position'] == -1]
    fig.add_trace(go.Scatter(
        x=sell_signals.index, 
        y=sell_signals['Close'] * 1.02,
        name='Sell Signal',
        mode='markers',
        marker=dict(color='red', size=12, symbol='triangle-down')
    ))
    
    # 配置图表
    fig.update_layout(
        title=f'{ticker} Price with MA Crossover Signals',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示交易信号详情
    col_buy, col_sell = st.columns(2)
    with col_buy:
        st.write(f"Buy Signals ({len(buy_signals)}):")
        st.dataframe(buy_signals[['Close', 'MA5', 'MA20']].style.highlight_max(axis=0))
    with col_sell:
        st.write(f"Sell Signals ({len(sell_signals)}):")
        st.dataframe(sell_signals[['Close', 'MA5', 'MA20']].style.highlight_min(axis=0))
    
    # 计算详细收益指标
    total_bh_return = (data['Cumulative Buy&Hold'].iloc[-1] / 100 -1) *100
    total_strat_return = (data['Cumulative Strategy'].iloc[-1] /100 -1)*100
    num_trades = len(buy_signals)
    
    # 最终收益表格
    st.subheader("Backtest Results")
    results_df = pd.DataFrame({
        'Metric': [
            'Initial Investment Value',
            'Final Buy & Hold Value', 
            'Final Strategy Value', 
            'Total Buy & Hold Return (%)',
            'Total Strategy Return (%)',
            'Strategy Outperformance (%)',
            'Number of Trades'
        ],
        'Value': [
            100,
            round(data['Cumulative Buy&Hold'].iloc[-1], 2),
            round(data['Cumulative Strategy'].iloc[-1], 2),
            round(total_bh_return, 2),
            round(total_strat_return, 2),
            round(total_strat_return - total_bh_return, 2),
            num_trades
        ]
    })
    st.dataframe(results_df)