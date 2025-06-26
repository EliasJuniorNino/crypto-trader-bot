import os
import argparse
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

# --- Argumentos de linha de comando ---
parser = argparse.ArgumentParser(description="Previsão com Random Forest para cripto")
parser.add_argument('--coin', type=str, required=True, help='Símbolo da moeda, ex: BTC, ETH')
args = parser.parse_args()

COIN = args.coin.upper()

# --- Variáveis de ambiente ---
load_dotenv()
DATASET_DIR = os.getenv("DATASET_DIR")

# --- Carrega dados ---
x_path = f"{DATASET_DIR}/dataset_full.csv"
if not os.path.exists(x_path):
    raise FileNotFoundError(f"Arquivo de X não encontrado: {x_path}")
dfx = pd.read_csv(x_path)

if 'OpenTime' not in dfx.columns:
    raise ValueError("dataset_full.csv deve conter a coluna 'OpenTime'")

y_path = f"{DATASET_DIR}/dataset_y_{COIN}.csv"
if not os.path.exists(y_path):
    raise FileNotFoundError(f"Arquivo de Y não encontrado: {y_path}")
dfy = pd.read_csv(y_path)

if dfy.shape[1] != 1:
    raise ValueError("dataset_y deve conter exatamente uma coluna (ex: 'Close')")

dfx['OpenTime'] = pd.to_datetime(dfx['OpenTime'])
dfx.set_index('OpenTime', inplace=True)

# --- Normaliza dados ---
scaler_x = MinMaxScaler()
scaler_y = MinMaxScaler()
scaled_x_data = scaler_x.fit_transform(dfx)
scaled_y_data = scaler_y.fit_transform(dfy)

# --- Treina Random Forest ---
print(f"[INFO] Treinando modelo para {COIN}...")
model_rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model_rf.fit(scaled_x_data, scaled_y_data.ravel())

# --- Salva o modelo ---
model_dir = f"{DATASET_DIR}/models/forest"
os.makedirs(model_dir, exist_ok=True)
joblib.dump(model_rf, f"{model_dir}/{COIN}_model_rf.pkl")
joblib.dump(scaler_x, f"{model_dir}/{COIN}_scaler_x.pkl")
joblib.dump(scaler_y, f"{model_dir}/{COIN}_scaler_y.pkl")

# --- Previsões ---
pred_rf_scaled = model_rf.predict(scaled_x_data)

# --- Inverte escala ---
def inverse_transform_column(scaled_column, scaler):
    return scaler.inverse_transform(scaled_column.reshape(-1, 1)).ravel()

pred_rf = inverse_transform_column(pred_rf_scaled, scaler_y)
real = inverse_transform_column(scaled_y_data, scaler_y)

# --- Métricas ---
rmse = np.sqrt(mean_squared_error(real, pred_rf))
mae = mean_absolute_error(real, pred_rf)

# --- Salva métricas em CSV ---
metrics_df = pd.DataFrame([{
    'coin': COIN,
    'rmse': round(rmse, 4),
    'mae': round(mae, 4)
}])
metrics_df.to_csv(f"{model_dir}/{COIN}_metrics.csv", index=False)

print(f"[INFO] RMSE: {rmse:.4f} | MAE: {mae:.4f}")
print(f"[INFO] Modelo salvo em: {model_dir}/{COIN}_model_rf.pkl")
