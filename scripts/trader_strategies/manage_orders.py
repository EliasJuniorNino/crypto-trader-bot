import datetime
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_LIMIT
import mysql.connector
import logging
from mysql.connector import Error
import os
import pandas as pd
from typing import Dict, TypedDict, List
import time
import numpy as np

# Configure o DB
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST"),
    "port": int(os.getenv("DATABASE_PORT", 3306)),  # Valor padrão 3306 se não definido
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_DBNAME")
}

# Configure suas chaves da Binance
API_KEY = os.getenv("BINANCE_API_KEY")  # ou substitua diretamente por sua chave
API_SECRET = os.getenv("BINANCE_API_SECRET")

def connect_db():
    """Conecta ao banco de dados e retorna a conexão."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logging.info("Conexão com o banco de dados estabelecida.")
            return connection
    except Error as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        return None

# Inicializa o cliente
client = Client(API_KEY, API_SECRET)

class WalletBalance(TypedDict):
    asset: str
    free: float
    locked: float
    
class AssetBalance(TypedDict):
    symbol: str
    price: float
    
class AssetPredict(TypedDict):
    min: float
    max: float
    
class OrderPredict(TypedDict):
    to_buy: bool

def get_current_balances(coin_names) -> Dict[str, AssetBalance]:
    current_balances = {}

    for coin in coin_names:
        symbol = f"{coin}USDT"
        try:
            ticker = client.get_symbol_ticker(symbol=symbol)
            current_balances[coin] = ticker
        except Exception as e:
            print(f"Erro ao obter preço para {symbol}: {e}")
            current_balances[coin] = None  # ou continue, se preferir ignorar os que falharem

    return current_balances

def get_predict() -> tuple[Dict[str, AssetPredict], List[str]]:
    df = pd.read_csv("data/predict.csv")

    if df.empty or df.shape[0] == 0:
        print("Arquivo predict.csv está vazio ou mal formatado.")
        return {}

    row = df.iloc[0]  # assumimos que só há uma linha com as previsões
    predictions = {}
    coin_names = []

    for col in df.columns:
        if "_min_value" in col:
            symbol = col.replace("_min_value", "")
            predictions.setdefault(symbol, {})["min"] = row[col]
            if symbol not in coin_names:
                coin_names.append(symbol)
        elif "_max_value" in col:
            symbol = col.replace("_max_value", "")
            predictions.setdefault(symbol, {})["max"] = row[col]
            if symbol not in coin_names:
                coin_names.append(symbol)

    return (predictions, coin_names)

def buy_or_update(symbol, quantity, price_usd, predicted_percent):
    db_connection = connect_db()
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, operation, quantity, price_usd, predicted_percent)
        VALUES (%s, %s, %s, %s, %s)
    """, (symbol, 'BUY', quantity, price_usd, predicted_percent))
    db_connection.commit()
    cursor.close()
    db_connection.close()

def sell_or_update(symbol, quantity, price_usd, predicted_percent):
    db_connection = connect_db()
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, operation, quantity, price_usd, predicted_percent)
        VALUES (%s, %s, %s, %s, %s)
    """, (symbol, 'SELL', quantity, price_usd, predicted_percent))
    db_connection.commit()
    cursor.close()
    db_connection.close()

def main():
    wallet_balances: List[WalletBalance] = client.get_account()['balances']
    predictions, prediction_coin_names = get_predict()
    coin_balances = get_current_balances(prediction_coin_names)
    predict_win_loss: Dict[str, float] = {}
    
    for coin_name in prediction_coin_names:
        current_value = np.float64(coin_balances[coin_name]["price"])
        pred_min = predictions[coin_name]['min']
        pred_max = predictions[coin_name]['min']
        
        diff_pred_min = (abs(current_value - pred_min) / current_value) * 100
        diff_pred_max = (abs(current_value - pred_max) / current_value) * 100
        
        secure_range = 1.0
        
        if current_value + secure_range < pred_min:
            predict_win_loss[coin_name] = diff_pred_min
        elif current_value - secure_range > pred_max:
            predict_win_loss[coin_name] = diff_pred_max * -1
            
    # Ordena pelo valor
    sorted_items = sorted(predict_win_loss.items(), key=lambda item: item[1])
    # Obtém a lista de ativos da wallet
    wallet_assets = {item['asset'] for item in wallet_balances if float(item['free']) > 0}
    sorted_items_in_wallet = [
        item for item in sorted_items 
        if any(item[0].startswith(asset) for asset in wallet_assets)
    ]

    # 5 menores + 5 maiores
    coins_to_buy = sorted_items[-5:]
    coins_to_sell = [
        item for item in sorted_items_in_wallet
        if item[1] < 0
    ]
    
    for (coin, predicted_percent) in coins_to_buy:
        quantity = 0
        price_usd = coin_balances[coin]["price"]
        buy_or_update(coin, quantity, price_usd, predicted_percent)
    
    for (coin, predicted_percent) in coins_to_sell:
        quantity = 0
        price_usd = coin_balances[coin]["price"]
        sell_or_update(coin, quantity, price_usd, predicted_percent)


if __name__ == "__main__":
    main()
