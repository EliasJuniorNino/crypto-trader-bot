import os
import argparse
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
DATA_DIR = os.getenv("DATA_DIR")

# --- Carrega dados ---
df = pd.read_csv(f"{DATA_DIR}/dataset_full.csv")

if f"{COIN}Close" not in df.columns:
    raise ValueError(f"Coluna {COIN}Close não encontrada no CSV.")

df = df[['OpenTime', f"{COIN}Close", 'fear_api_alternative_me', 'fear_coinmarketcap']]
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
def calc_metrics(true, pred, name):
    rmse = np.sqrt(mean_squared_error(true, pred))
    mae = mean_absolute_error(true, pred)
    print(f"{name} - RMSE: {rmse:.3f}, MAE: {mae:.3f}")
    return rmse, mae

rmse_rf, mae_rf = calc_metrics(real, pred_rf, "Random Forest")

# --- Gráfico ---
plt.figure(figsize=(14,7))
plt.plot(real, label='Preço Real', color='black')
plt.plot(pred_rf, label='Random Forest Previsto', color='green')
plt.title(f'Previsão de Preço - {COIN} com Random Forest')
plt.xlabel('Tempo')
plt.ylabel('Preço em USD')
plt.legend()
plt.tight_layout()
plt.savefig("previsao_random_forest.png")
