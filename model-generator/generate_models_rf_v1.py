import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

# --- Variáveis de ambiente ---
load_dotenv()
DATASET_DIR = os.getenv("DATASET_DIR")

# --- Carrega dados ---
df = pd.read_csv(f"{DATASET_DIR}/dataset_percent.csv")

# Encontrar colunas de preços
price_columns = [col for col in df.columns if col.endswith(('High', 'Low'))]
if not price_columns:
    raise ValueError("Nenhuma coluna de preços (High/Low) encontrada no dataset.")

coins = sorted(list(set(col.replace('High', '').replace('Low', '') for col in price_columns)))
coins = [coin for coin in coins if coin]  # Remove strings vazias

for coin in coins:
    if f"{coin}_Close" not in df.columns:
        raise ValueError(f"Coluna {coin}_Close não encontrada no CSV.")

    df = df[['OpenTime', f"{coin}_Close", 'fear_api_alternative_me', 'fear_coinmarketcap']]
    df['OpenTime'] = pd.to_datetime(df['OpenTime'])
    df.set_index('OpenTime', inplace=True)

    # --- Normaliza dados ---
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)

    LOOK_BACK = 60

    def create_sequences_rf(data, look_back=LOOK_BACK):
        X, y = [], []
        for i in range(look_back, len(data)):
            X.append(data[i-look_back:i].flatten())
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    # --- Divide treino e teste ---
    split_idx = int(len(scaled_data)*0.8)
    train_data = scaled_data[:split_idx]
    test_data = scaled_data[split_idx - LOOK_BACK:]

    X_train, y_train = create_sequences_rf(train_data)
    X_test, y_test = create_sequences_rf(test_data)

    # --- Treina Random Forest ---
    model_rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model_rf.fit(X_train, y_train)

    # --- Salva o modelo ---
    model_dir = f"{DATASET_DIR}/models/forest"
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model_rf, f"{model_dir}/{coin}_rf.pkl")

    # --- Previsões ---
    pred_rf_scaled = model_rf.predict(X_test)

    # --- Inverte escala ---
    def inverse_transform(scaled_values, scaled_full_data):
        full = np.zeros((len(scaled_values), scaled_full_data.shape[1]))
        full[:, 0] = scaled_values
        return scaler.inverse_transform(full)[:, 0]

    pred_rf = inverse_transform(pred_rf_scaled, scaled_data)
    real = inverse_transform(y_test, scaled_data)

    # --- Métricas ---
    rmse = np.sqrt(mean_squared_error(real, pred_rf))
    mae = mean_absolute_error(real, pred_rf)

    # --- Salva métricas em CSV ---
    metrics_df = pd.DataFrame([{
        'coin': coin,
        'rmse': round(rmse, 2),
        'mae': round(mae, 2)
    }])
    metrics_df.to_csv(f"{model_dir}/{coin}_metrics.csv", index=False)
