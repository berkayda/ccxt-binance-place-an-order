import ccxt
import config
import pandas as pd
from datetime import datetime
import time
import requests


exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

symbol = "BTCUSDT"
leverage = 30
futures_usdt_amount = 5 #This is the USDT value of your position

def get_current_price(symbol=symbol):
    max_attempts = 10 
    attempt = 1
    while attempt <= max_attempts:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            print("Price: " + str(price) + " USDT")
            return price
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_attempts:
                print("Trying to get the current price...")
                time.sleep(10)
        attempt += 1
    if attempt > max_attempts:
        print("Attempt > Max. Attempts (Please try later.)")
        return None

def set_leverage(symbol=symbol, leverage=leverage):
    max_attempts = 10
    attempt = 1
    while attempt <= max_attempts:
        try:
            global leverage_response
            exchange.load_markets()
            market = exchange.market(symbol)
            leverage_response = exchange.fapiPrivatePostLeverage({
                'symbol': market['id'],
                'leverage': leverage,
            })
            print(leverage_response)
            try:
                response = exchange.fapiprivate_post_margintype({
                    'symbol': market['id'],
                    'marginType': 'ISOLATED',
                })
                print(response)
            except ccxt.MarginModeAlreadySet:
                print('Margin mode is already set to ISOLATED. No need to change.')
            return
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_attempts:
                print("Trying to set leverage...")
                time.sleep(5)
        attempt += 1
    if attempt > max_attempts:
        print("Attempt > Max. Attempts (Please try later.)")

#set_leverage(symbol, leverage) #example function usage

def place_order(symbol, side, type):
    if leverage_response['leverage'] == str(leverage):
        current_price = get_current_price()
        futures_amount = round(((futures_usdt_amount * leverage) / current_price) * 0.95, 2)  # decimal number amount of after the comma
        #futures_amount is exact quantity of your position.
        print('Leverage is set.')
        order = exchange.fapiPrivatePostOrder({
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': futures_amount,
            'price': get_current_price(),
            'timeInForce': 'GTC'  # valid until cancel
        })
        if 'orderId' in order and 'clientOrderId' in order:
            print(order['symbol'] + "\n" + "Price: " + order['price'] + "\n" + order['side'] + "\n" +
                  "Order ID: " + order['orderId'] + "\n" + "Client Order ID: " + order['clientOrderId'])

        else:
            print("There is an error.")
        while True:
            global order_status
            order_status = exchange.fapiPrivateGetOrder({
                'symbol': symbol,
                'orderId': order['orderId']
            })
            print(order_status)
            if order_status['status'] == 'FILLED':
                entry_price = order['price']
                print("FILLED.")
                break

            elif order_status['status'] == 'CANCELED':
                print("CANCELED.")
                break

            elif order_status['status'] == 'NEW':
                print("Not yet Filled.")
                time.sleep(20)

            else:
                print("Order is NOT filled.")
                time.sleep(20)
    else:
        print("The order could not be placed because there was a problem while adjusting the leverage.")

#place_order(symbol, 'BUY', 'LIMIT') #example function usage
