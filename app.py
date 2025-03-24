from flask import Flask, render_template_string
import requests
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# HTML şablonu (İngilizce)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BNB Prediction Bot</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .prediction { font-size: 24px; margin: 20px; }
        .up { color: green; }
        .down { color: red; }
        .neutral { color: gray; }
    </style>
</head>
<body>
    <h1>BNB Prediction Bot</h1>
    <p>Last Update: {{ time }}</p>
    <p>Current Price: {{ price }} USDT</p>
    <p class="prediction {{ prediction.lower() }}">Prediction: {{ prediction }}</p>
    <script>
        setTimeout(function() { location.reload(); }, 240000);
    </script>
</body>
</html>
"""

def get_binance_klines():
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BNBUSDT", "interval": "1m", "limit": 200}  # 1 dakikalık veriler, son 200 mum
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=["open_time", "open", "high", "low", "close", "volume",
                                     "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore"])
    
    # Verileri float'a çevir
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # 1 dakikalık verileri 4 dakikalık mumlara dönüştür
    df.set_index("open_time", inplace=True)
    df_4m = df.resample("4min").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    return df_4m.reset_index()

def predict_price(df):
    sma_short = df["close"].rolling(window=10).mean().iloc[-1]
    sma_long = df["close"].rolling(window=20).mean().iloc[-1]
    current_price = df["close"].iloc[-1]
    if sma_short > sma_long and current_price > sma_short:
        return "UP"
    elif sma_short < sma_long and current_price < sma_short:
        return "DOWN"
    else:
        return "NEUTRAL"

@app.route('/')
def home():
    df = get_binance_klines()
    prediction = predict_price(df)
    current_price = df["close"].iloc[-1]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(INDEX_HTML, time=current_time, price=current_price, prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)