import os
import requests
import pandas as pd
import numpy as np
from io import StringIO
import zipfile, io
from datetime import datetime

GOLD_MARKET_CODE = "088691"

def get_gold_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(price, 2)
    except Exception as e:
        print(f"שגיאה בזהב: {e}")
        return None

def get_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        btc = round(data["bitcoin"]["usd"], 2)
        btc_change = round(data["bitcoin"]["usd_24h_change"], 2)
        eth = round(data["ethereum"]["usd"], 2)
        eth_change = round(data["ethereum"]["usd_24h_change"], 2)
        return btc, btc_change, eth, eth_change
    except Exception as e:
        print(f"שגיאה בקריפטו: {e}")
        return None, None, None, None

def get_fear_greed():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
