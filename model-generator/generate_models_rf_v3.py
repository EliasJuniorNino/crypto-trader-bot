import os
import numpy as np
import pandas as pd
import joblib

from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

# --- Variáveis de ambiente ---
load_dotenv()
DATASET_DIR = os.getenv("DATASET_DIR")

# --- Carrega dados ---
df = pd.read_csv(f"{DATASET_DIR}/dataset_percent.csv")

# Encontrar colunas de preços
price_columns = [col for col in df.columns if col.endswith(('_PercentHigh', '_PercentLow'))]
if not price_columns:
    raise ValueError("Nenhuma coluna de preços (_PercentHigh/_PercentLow) encontrada no dataset.")

coins = sorted(list(set(col.replace('_PercentHigh', '').replace('_PercentLow', '') for col in price_columns)))
coins = [coin for coin in coins if coin]  # Remove strings vazias

df['OpenTime'] = pd.to_datetime(df['OpenTime'])
df.set_index('OpenTime', inplace=True)

# --- Normaliza dados ---
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df)

for coin in coins:
    LOOK_BACK = 30

    def create_sequences_rf(data, target_indices, look_back=LOOK_BACK):
        X, y = [], []
        for i in range(look_back, len(data)):
            X.append(data[i - look_back:i].flatten())
            y.append([data[i, target_indices[0]], data[i, target_indices[1]]])
        return np.array(X), np.array(y)
    
    # Divide dados
    split_idx = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:split_idx]
    test_data = scaled_data[split_idx - LOOK_BACK:]

    high_col = f"{coin}_PercentHigh"
    low_col = f"{coin}_PercentLow"
    target_indices = [df.columns.get_loc(high_col), df.columns.get_loc(low_col)]
    X_train, y_train = create_sequences_rf(train_data, target_indices)
    X_test, y_test = create_sequences_rf(test_data, target_indices)

    # Modelo multi-saída
    base_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model_rf = MultiOutputRegressor(base_model)
    model_rf.fit(X_train, y_train)

    # Salva modelo
    model_dir = f"{DATASET_DIR}/models/forest"
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model_rf, f"{model_dir}/{coin}_rf.pkl")

    # Previsão
    pred_rf_scaled = model_rf.predict(X_test)

    # Inverter escala
    def inverse_transform(scaled_values, scaled_full_data, indices):
        full = np.zeros((len(scaled_values), scaled_full_data.shape[1]))
        for i, idx in enumerate(indices):
            full[:, idx] = scaled_values[:, i]
        return scaler.inverse_transform(full)[:, indices]

    pred_rf = inverse_transform(pred_rf_scaled, scaled_data, target_indices)
    real = inverse_transform(y_test, scaled_data, target_indices)

    # Métricas separadas para High e Low
    rmse_high = np.sqrt(mean_squared_error(real[:, 0], pred_rf[:, 0]))
    mae_high = mean_absolute_error(real[:, 0], pred_rf[:, 0])
    rmse_low = np.sqrt(mean_squared_error(real[:, 1], pred_rf[:, 1]))
    mae_low = mean_absolute_error(real[:, 1], pred_rf[:, 1])

    # Salvar métricas
    metrics_df = pd.DataFrame([{
        'coin': coin,
        'rmse_high': round(rmse_high, 2),
        'mae_high': round(mae_high, 2),
        'rmse_low': round(rmse_low, 2),
        'mae_low': round(mae_low, 2)
    }])
    metrics_df.to_csv(f"{model_dir}/{coin}_metrics.csv", index=False)
