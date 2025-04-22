import pandas as pd
import os
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_crypto_min_max():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        crypto_min_max = {}

        for item in data:
            symbol = item["symbol"]
            high_price = float(item["highPrice"])
            low_price = float(item["lowPrice"])
            crypto_min_max[symbol] = {"max": high_price, "min": low_price}

        return crypto_min_max
    else:
        print("Erro ao acessar a API da Binance")
        return None


def load_model(coin):
    """Carrega o modelo treinado a partir de um arquivo."""
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

def predict_prices(model, df, coin):
    """Usa o modelo carregado para prever os preços da criptomoeda."""
    try:
        # Separa features (X) e target (y)
        X = df.copy()
        y = df[[f"{coin}_max_price", f"{coin}_min_price"]]

        # Faz as previsões
        y_pred = model.predict(X)

        # Avalia as previsões
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        logging.info(f"Previsões para {coin} com MSE: {mse:.4f}, MAE: {mae:.4f}")

        return {
            'coin': coin,
            'predict': y_pred[-1]
        }

    except Exception as e:
        logging.error(f"Erro ao fazer previsões para {coin}: {e}")


if __name__ == "__main__":
    min_max_data = get_crypto_min_max()

    if min_max_data:
        for symbol, prices in min_max_data.items():
            print(f"{symbol}: Máximo: {prices['max']} | Mínimo: {prices['min']}")
