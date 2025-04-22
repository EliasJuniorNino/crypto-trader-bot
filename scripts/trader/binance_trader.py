import os
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
import requests
from decimal import Decimal, getcontext
import pandas as pd
import numpy as np

from database import connect_db

# Configuração de precisão decimal
getcontext().prec = 50

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_cryptos_names():
    db_conn = connect_db()
    cursor = db_conn.cursor()
    
    SQL_QUERY = "SELECT c.symbol FROM cryptos c JOIN exchanges_cryptos ec ON c.id = ec.crypto_id JOIN exchanges e ON ec.exchange_id = e.id WHERE LOWER(e.name) LIKE '%binance%';"
    cursor.execute(SQL_QUERY)
    criptos = cursor.fetchall()
    criptos_names = []
    for (coin,) in criptos:
        criptos_names.append(coin)
    return criptos_names

def get_crypto_min_max():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        crypto_min_max = {}

        criptos_names = get_cryptos_names()

        for item in data:
            symbol = item["symbol"]
            if symbol not in criptos_names:
                continue
            high_price = Decimal(item["highPrice"])
            low_price = Decimal(item["lowPrice"])
            crypto_min_max[symbol] = {"max": high_price, "min": low_price}

        return crypto_min_max
    else:
        logging.error("Erro ao acessar a API da Binance")
        return None

def load_model(coin):
    try:
        model_path = f"models/model_{coin}.pkl"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            logging.info(f"Modelo para {coin} carregado com sucesso.")
            return model
        else:
            logging.error(f"Arquivo do modelo não encontrado: {model_path}")
            return None
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo para {coin}: {e}")
        return None
    
def get_data_frame():
    try:
        df_path = "data/dataset.csv"
        if os.path.exists(df_path):
            df = pd.read_csv(df_path)
            logging.info(f"DataFrame carregado de {df_path} com sucesso.")
            return df
        else:
            logging.error(f"Arquivo CSV não encontrado: {df_path}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Erro ao carregar o DataFrame: {e}")
        return pd.DataFrame()

def predict_prices(model, df, coin):
    try:
        X = df.drop(columns=[f"{coin}_max_price", f"{coin}_min_price"], errors='ignore').astype(np.float64)
        y = df[[f"{coin}_max_price", f"{coin}_min_price"]].astype(np.float64)

        y_pred = model.predict(X)

        mse = Decimal(str(mean_squared_error(y, y_pred)))
        mae = Decimal(str(mean_absolute_error(y, y_pred)))
        logging.info(f"Previsões para {coin} com MSE: {mse:.50f}, MAE: {mae:.50f}")

        return {
            'coin': coin,
            'predict': [Decimal(str(val)) for val in y_pred[-1]]
        }

    except Exception as e:
        logging.error(f"Erro ao fazer previsões para {coin}: {e}")
        return None

if __name__ == "__main__":
    min_max_data = get_crypto_min_max()

    # Exemplo: simulando um DataFrame de entrada
    # Este trecho precisa ser substituído por dados reais
    df_simulado = pd.DataFrame(get_data_frame())

    if min_max_data:
        for symbol in min_max_data.keys():
            model = load_model(symbol)
            if model:
                result = predict_prices(model, df_simulado, symbol)
                if result:
                    print(f"Previsão para {symbol}:")
                    print(f"  Máximo previsto: {result['predict'][0]:.50f}")
                    print(f"  Mínimo previsto: {result['predict'][1]:.50f}")
