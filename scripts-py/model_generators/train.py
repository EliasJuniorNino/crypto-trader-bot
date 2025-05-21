import pandas as pd
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import logging

# 2025,2,4,72,45,2664.92,2838

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_data(file_path):
    """Carrega os dados a partir de um dataset (CSV)."""
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
        logging.info(f"Columns {df.columns}")

        # Identifica colunas de moedas
        coin_names = set()
        for col in df.columns:
            if "_max_value" in col or "_min_value" in col:
                coin_names.add(col.split("_")[0])

        logging.info("Dados carregados com sucesso.")
        return df, list(coin_names)

    except Exception as e:
        logging.error(f"Erro ao carregar dados do dataset: {e}")
        return None, None

def train_model(df, coin):
    """Treina um modelo de Random Forest e salva o arquivo."""
    try:
        X = df.copy()
        y = df[[f"{coin}_max_value", f"{coin}_min_value"]].shift(-1)

        X = X.iloc[:-1]
        y = y.iloc[:-1]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(n_estimators=500, max_depth=50, random_state=42, n_jobs=-1))
        ])

        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        logging.info(f"Modelo treinado para {coin} com MSE: {mse:.4f}")

        os.makedirs("models", exist_ok=True)
        model_path = f"models/model_{coin}.pkl"
        joblib.dump(pipeline, model_path)
        logging.info(f"Modelo salvo em {model_path}")

    except Exception as e:
        logging.error(f"Erro ao treinar o modelo para {coin}: {e}")

def predict_last_row(df, coin):
    """Prevê os valores max e min para a última linha do dataset."""
    try:
        model_path = f"models/model_{coin}.pkl"
        if not os.path.exists(model_path):
            logging.warning(f"Modelo não encontrado para {coin}.")
            return

        model = joblib.load(model_path)

        last_row = df.iloc[[-1]]  # DataFrame com a última linha
        prediction = model.predict(last_row)

        return {
            "coin": coin,
            "predicted_max": round(prediction[0][0], 50),
            "predicted_min": round(prediction[0][1], 50)
        }

    except Exception as e:
        logging.error(f"Erro ao prever a última linha para {coin}: {e}")

def main():
    file_path = "data/dataset.csv"
    df, coin_names = load_data(file_path)

    predictMap = {}
    if df is not None and coin_names:
        for coin in coin_names:
            pass
            train_model(df.copy(), coin)
    
        for coin in coin_names:
            predictMap[coin] = predict_last_row(df.copy(), coin)
    print(predictMap)

if __name__ == "__main__":
    main()
