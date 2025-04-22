import pandas as pd
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import logging

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
        # Separa features (X) e target (y)
        X = df.copy()
        y = df[[f"{coin}_max_value", f"{coin}_min_value"]].shift(-1)

        # Remove a última linha (NaN devido ao shift)
        X = X.iloc[:-1]
        y = y.iloc[:-1]

        # Divide os dados em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Cria o pipeline de pré-processamento e modelo
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(n_estimators=500, max_depth=50, random_state=42, n_jobs=-1))
        ])

        # Treina o modelo
        pipeline.fit(X_train, y_train)

        # Avalia o modelo
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        logging.info(f"Modelo treinado para {coin} com MSE: {mse:.4f}")

        # Salva o modelo
        os.makedirs("models", exist_ok=True)
        model_path = f"models/model_{coin}.pkl"
        joblib.dump(pipeline, model_path)
        logging.info(f"Modelo salvo em {model_path}")

    except Exception as e:
        logging.error(f"Erro ao treinar o modelo para {coin}: {e}")

def main():
    """Função principal para carregar dados e treinar modelos."""
    file_path = "../dataset.csv"  # Nome do arquivo do dataset
    df, coin_names = load_data(file_path)

    if df is not None and coin_names:
        for coin in coin_names:
            train_model(df.copy(), coin)

if __name__ == "__main__":
    main()
