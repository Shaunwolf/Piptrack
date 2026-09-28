# tosin2013/fibonacci_price_target (space)

```json
{
  "kind": "space",
  "id": "tosin2013/fibonacci_price_target",
  "url": "https://huggingface.co/spaces/tosin2013/fibonacci_price_target",
  "meta": {
    "tags": [
      "gradio",
      "region:us"
    ],
    "likes": 0,
    "sdk": "gradio",
    "cardData": {
      "license": "apache-2.0",
      "title": "Fibonacci Price Targets",
      "sdk": "gradio",
      "emoji": "\ud83d\udcc8",
      "colorFrom": "green",
      "colorTo": "purple"
    },
    "lastModified": "2024-02-18T03:24:53.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": ".gitattributes",
      "size": 1519,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 807,
      "type": "file"
    },
    {
      "path": "app.py",
      "size": 13601,
      "type": "file"
    },
    {
      "path": "fibonacci_price_targets.ipynb",
      "size": 158116,
      "type": "file"
    },
    {
      "path": "requirements.txt",
      "size": 96,
      "type": "file"
    }
  ]
}
```

## README

---
license: apache-2.0
title: Fibonacci Price Targets 
sdk: gradio
emoji: 📈
colorFrom: green
colorTo: purple
---
# Fibonacci Price Targets
This repository contains a Python script that calculates potential price targets for financial assets based on Fibonacci retracement and extension levels.

## Key Features
* Flexible Inputs:  The script allows users to specify the following:

  * Asset's historical price data (e.g., OHLC data in a CSV format)
  * The starting and ending points for the Fibonacci calculation
  * Fibonacci retracement levels (e.g., 0.236, 0.382, 0.5, 0.618, 0.786)
  * Fibonacci extension levels (e.g., 1.0, 1.382, 1.618, 2.618)
* Clear Visualization: The script generates a plot of the asset's price chart with the calculated Fibonacci levels overlaid, aiding in visual analysis.

## app.py

```
import gradio as gr
import requests
import pandas as pd
import math
import os
import matplotlib.pyplot as plt
from alpha_vantage.timeseries import TimeSeries

#symbol = 'NRDS'
#target_profit_price = 9.34
#interval = 'daily'  # Specify the desired interval ('intraday', 'daily', 'weekly')
#start_date = '2023-01-01'  # Specify the start date for historical data
#buy_signal = False

def get_current_stock_price(api_key, symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    response = requests.get(url)
    print(response)
    data = response.json()
    return data['c']  # Current price

finnhub_api_key=os.environ['FINHUB_API_KEY']


def calculate_fibonacci_retracements(high, low):
    # Adjust the Fibonacci ratios as needed
    fibonacci_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]  # Example adjusted ratios
    fibonacci_retracements = []
    for i in range(40):
        fibonacci_level = round((i+1)/(len(fibonacci_ratios)+1), 2) * fibonacci_ratios[i % len(fibonacci_ratios)]
        fibonacci_retracements.append(fibonacci_level)
    fibonacci_levels = {}
    for r in fibonacci_retracements:
        fibonacci_levels[f"{r * 100:.0f}%"] = round((low + high) - ((high - low) * r), 2)
    return fibonacci_levels

from alpha_vantage.timeseries import TimeSeries

def fetch_historical_data(symbol, interval, output_size='compact', start_date=None):
    # Replace with your AlphaVantage API key
    api_key = os.environ['ALPHA_VANTAGE_API_KEY'] 

    # Initialize the TimeSeries object
    ts = TimeSeries(key=api_key, output_format='json')

    # Map interval to the corresponding AlphaVantage function name
    interval_mapping = {
        'intraday': 'TIME_SERIES_INTRADAY',
        'daily': 'TIME_SERIES_DAILY',
        'weekly': 'TIME_SERIES_WEEKLY'
    }

    if interval not in interval_mapping:
        raise ValueError("Invalid interval. Supported intervals: 'intraday', 'daily', 'weekly'")

    # Define the function name based on the interval
    function_name = interval_mapping[interval]

    if interval == 'intraday':
        # Adjust the interval as needed
        interval = '5min'
    
    # Fetch historical data
    if interval == 'daily':
        historical_data, meta_data = ts.get_daily_adjusted(symbol=symbol, outputsize=output_size)
    elif interval == 'weekly':
        historical_data, meta_data = ts.get_weekly_adjusted(symbol=symbol)
    else:
        # For intraday, you can specify the interval (e.g., '5min')
        historical_data, meta_data = ts.get_intraday(symbol=symbol, interval=interval, outputsize=output_size)

    return historical_data

import numpy as np

def calculate_support_resistance_levels(symbol, interval='intraday', output_size='compact'):
    # Fetch historical price data from AlphaVantage
    historical_data = fetch_historical_data(symbol, interval, output_size)
    
    # Extract closing prices from historical data
    closing_prices = [float(data['4. close']) for data in historical_data.values()]
    print("Display historyical data")
    print(closing_prices)

    # Calculate moving averages (e.g., 50-day and 200-day)
    moving_average_50 = np.mean(closing_prices[-50:])
    moving_average_200 = np.mean(closing_prices[-200:])
    
    # Calculate support and resistance levels
    # You can customize your logic for defining these levels based on moving averages
    # For example, support could be defined as the 50-day moving average, and resistance could be the 200-day moving average
    support_level = moving_average_50
    resistance_level = moving_average_200
    
    return support_level, resistance_level

def calculate_entry_exit_points(symbol, target_profit_price, risk_percentage, account_balance, start_date, buy_signal_str):
    # Convert string inputs to correct data types
    print("Debugging information:")
   
    print("target_profit_price:", target_profit_price)
    print("risk_percentage:", risk_percentage)
    print("account_balance:", account_balance)
    
    current_price = get_current_stock_price(finnhub_api_key, symbol)
    print("current_price:", current_price)
    target_profit_price = float(target_profit_price)
    risk_percentage = float(risk_percentage)
    account_balance = float(account_balance)
    buy_signal = buy_signal_str == "Buy"
    print("buy_signal:", buy_signal)
    
    # Fetch swing high and swing low using symbol, interval, and start date
    swing_high, swing_low = get_swing_high_low(symbol, 'intraday', start_date)
    
    # Calculate Fibonacci levels
    fibonacci_levels = calculate_fibonacci_retracements(swing_high, swing_low)
    
    # Calculate support and resistance levels
    support_level, resistance_level = calculate_support_resistance_levels(symbol, 'intraday', start_date)
    
    # Calculate entry and stop loss based on support and resistance
    entry_point, stop_loss = calculate_entry_stop_loss(support_level, resistance_level, buy_signal)
    
    # Calculate position size based on risk percentage and account balance
    position_size = (risk_percentage / 100) * account_balance
    
    # Calculate take profit based on Fibonacci levels and target price
    take_profit, closest_levels = calculate_take_profit(target_profit_price, fibonacci_levels, buy_signal)
    
    # Calculate profit in dollars for take profit and stop loss
    if buy_signal:
        profit_take_profit = (take_profit - entry_point) * position_size
        profit_stop_loss = (entry_point - stop_loss) * position_size
    else:
        profit_take_profit = (entry_point - take_profit) * position_size
        profit_stop_loss = (stop_loss - entry_point) * position_size
    
    # Determine buy/sell flag
    buy_sell_flag = "Buy" if buy_signal else "Sell"
    
    return {
        'Ticker': symbol,
        'entry': entry_point,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'swing_high': swing_high,
        'swing_low': swing_low,
        'position_size': position_size,
        'profit_take_profit': profit_take_profit,
        'profit_stop_loss': profit_stop_loss,
        'fibonacci_levels': fibonacci_levels,
        'closest_levels': closest_levels,
        'support_level': support_level,
        'resistance_level': resistance_level,
        'buy_sell_flag': buy_sell_flag
    }

# Note: You would also need to adjust or create the calculate_profit function to handle profit calculation.

def calculate_entry_stop_loss(support_level, resistance_level, buy_signal):
    # Calculate entry and stop loss based on support and resistance
    if buy_signal:
        entry_point = support_level
        stop_loss = entry_point - (entry_point * 0.02)  # Adjust the percentage as needed
    else:
        entry_point = resistance_level
        stop_loss = entry_point + (entry_point * 0.02)  # Adjust the percentage as needed
    return entry_point, stop_loss

def calculate_take_profit(target_price, fibonacci_levels, buy_signal):
    # Calculate take profit based on Fibonacci levels and target price
    if buy_signal:
        closest_levels = {k: v for k, v in fibonacci_levels.items() if v > target_price}
        print("Closest Levels:")
        print(closest_levels)
        take_profit_fibonacci_level = max(closest_levels.keys())
        take_profit = closest_levels[take_profit_fibonacci_level]
    else:
        closest_levels = {k: v for k, v in fibonacci_levels.items() if v < target_price}
        print("Closest Levels:")
        print(closest_levels)
        if closest_levels:
            take_profit_fibonacci_level = min(closest_levels.keys())
            take_profit = closest_levels[take_profit_fibonacci_level]
        else:
            take_profit_fibonacci_level = 0
            take_profit = 0  # Assuming default level and price
    return take_profit, closest_levels

def get_swing_high_low(symbol, interval, start_date):
    print(symbol, interval, start_date)
    # Fetch historical price data from AlphaVantage
    historical_data = fetch_historical_data(symbol,interval, start_date=start_date)
    print("prining historical data")
    print(historical_data)

    # Initialize variables to store swing high and swing low prices
    swing_high = None
    swing_low = None

    # Iterate through historical data to find swing high and swing low
    for date, price_data in historical_data.items():
        high_price = float(price_data['2. high'])
        low_price = float(price_data['3. low'])

        if swing_high is None or high_price > swing_high:
            swing_high = high_price

        if swing_low is None or low_price < swing_low:
            swing_low = low_price

    return swing_high, swing_low


import gradio as gr

def interface_wrapper(symbol, target_profit_price, risk_percentage, account_balance, start_date, buy_signal):
    # Your function logic here
    
    # Dummy return for demonstration purposes
    return {
        "Entry Point": 100,
        "Stop Loss": 90,
        "Take Profit": 110,
        "Position Size": 1000,
        "Profit (Take Profit)": 100,
        "Profit (Stop Loss)": -100,
        "Fibonacci Levels": {"38.2%": 95, "61.8%": 105},
        "Buy/Sell Flag": buy_signal
    }

# Ensure inputs to Gradio interface are in the correct order and use the correct components
demo = gr.Interface(
    fn=calculate_entry_exit_points,
    inputs=[
        gr.Textbox(label="Stock Symbol"),  # symbol
        gr.Number(label="Target Profit Price"),  # target_profit_price
        gr.Slider(label="Risk Percentage", minimum=0, maximum=100, step=0.1),  # risk_percentage, with default at 2%
        gr.Number(label="Account Balance"),  # account_balance, with default
        gr.Textbox(label="Start Date", placeholder="YYYY-MM-DD"),  # start_date, with default
        gr.Radio(choices=["Buy", "Sell"], label="Buy/Sell Signal")  # buy_signal, with default
    ],
    outputs=gr.JSON(label="Results"),
    description="Enter the necessary information to calculate entry and exit points for stock trading."
)

demo.launch(share=True)  # share=True to create a public link


def plot_trade(entry, stop_loss, take_profit, fibonacci_json):
    # Parse the Fibonacci levels from JSON
    fibonacci_levels = json.loads(fibonacci_json)

    # Prepare data for plotting
    fib_levels = list(fibonacci_levels.values())
    fib_labels = list(fibonacci_levels.keys())

    # Initialize the plot
    plt.figure(figsize=(10, 6))
    plt.title("Trade Setup with Fibonacci Levels")
    
    # Plot Fibonacci levels
    for i, level in enumerate(fib_levels):
        plt.axhline(y=level, linestyle='--', color='gray', alpha=0.5)
        plt.text(len(fib_labels) + 1, level, f"{fib_labels[i]}: {level}", verticalalignment='center')

    # Plot entry, stop_loss, and take_profit
    plt.axhline(y=entry, color='blue', label='Entry')
    plt.axhline(y=stop_loss, color='red', label='Stop Loss')
    plt.axhline(y=take_profit, color='green', label='Take Profit')
    
    plt.legend()
    plt.xlabel("Fibonacci Levels")
    plt.ylabel("Price")
    plt.tight_layout()

    # Save the plot to a temporary file and return its path
    plt_path = "/mnt/data/trade_setup.png"
    plt.savefig(plt_path)
    plt.close()
    
    return plt_path

# Example usage
#current_price = get_current_stock_price(finnhub_api_key, symbol)
# start_date = '2023-01-01' 
# swing_high, swing_low = get_swing_high_low(symbol, 'weekly', start_date)
# print(f"Swing High: {swing_high}, Swing Low: {swing_low}")
# risk_percentage = 1finnhub_api_key
# account_balance = 10000

# entry_exit_points = calculate_entry_exit_points(current_price=current_price, target_price=target_profit_price, risk_percentage=1, account_balance=10000, swing_high=swing_high, swing_low=swing_low,buy_signal=buy_signal)

# Printing the output
# print("Current Price:", current_price)
# print("Price Target:", target_profit_price)
# print("Entry Price:", entry_exit_points['entry'])
# print("Stop Loss:", entry_exit_points['stop_loss'])
# print("Take Profit:", entry_exit_points['take_profit'])
# print("Position Size:", entry_exit_points['position_size'])
# print("Profit (Take Profit): $", entry_exit_points['profit_take_profit'])
# print("Profit (Stop Loss): $", entry_exit_points['profit_stop_loss'])
# print("Fibonacci Levels:", entry_exit_points['fibonacci_levels'])
# Print the closest levels and their associated prices for debugging
# if buy_signal:
#     print(f"Closest levels for Buy (targeting {target_profit_price}): {entry_exit_points['closest_levels']}")
# else:
#     print(f"Closest levels for Sell (targeting {target_profit_price}): {entry_exit_points['closest_levels']}")
# print("Buy/Sell Flag:", entry_exit_points['buy_sell_flag'])


# Print the structure of entry_exit_points['closest_levels']

# Extract levels and prices from entry_exit_points['closest_levels'] dictionary
# levels = list(entry_exit_points['closest_levels'].keys())
# prices = list(entry_exit_points['closest_levels'].values())

# Create a bar chart
# plt.figure(figsize=(10, 6))
# plt.bar(levels, prices, color='blue' if buy_signal else 'red')
# plt.xlabel("Fibonacci Levels")
# plt.ylabel("Price")
# plt.title("Average Price at Fibonacci Levels")
# plt.xticks(rotation=45)

# Show the chart
# plt.show()

# print(entry_exit_points['closest_levels'])
# for key, value in entry_exit_points['closest_levels'].items():
#     print(f"Property: {key}, Value: {value}")
# Check if it's a buy or sell signal and adjust the title accordingly
# if buy_signal:
#     title = f"Closest Levels for Buy (targeting {target_profit_price})"
# else:
#     title = f"Closest Levels for Sell (targeting {target_profit_price})"

```

## requirements.txt

```
numpy
pandas
pandas_datareader
matplotlib
scipy
seaborn
alpha_vantage
gradio
gradio_client
boto3
```
