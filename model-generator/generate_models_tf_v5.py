import os
import argparse
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input

# --- Argumentos de linha de comando ---
parser = argparse.ArgumentParser(description="Comparativo LSTM x Random Forest para cripto")
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

def create_sequences_lstm(data, look_back=LOOK_BACK):
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

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

# Para LSTM
X_train_lstm, y_train_lstm = create_sequences_lstm(train_data)
X_test_lstm, y_test_lstm = create_sequences_lstm(test_data)

# Para Random Forest
X_train_rf, y_train_rf = create_sequences_rf(train_data)
X_test_rf, y_test_rf = create_sequences_rf(test_data)

# --- Treina LSTM ---
model_lstm = Sequential([
    Input(shape=(X_train_lstm.shape[1], X_train_lstm.shape[2])),
    LSTM(50, return_sequences=True),
    Dropout(0.2),
    LSTM(50),
    Dropout(0.2),
    Dense(1)
])
model_lstm.compile(optimizer='adam', loss='mean_squared_error')
model_lstm.fit(X_train_lstm, y_train_lstm, epochs=20, batch_size=32, validation_split=0.1, verbose=0)

# --- Treina Random Forest ---
model_rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model_rf.fit(X_train_rf, y_train_rf)

# --- Previsões ---
pred_lstm_scaled = model_lstm.predict(X_test_lstm).flatten()
pred_rf_scaled = model_rf.predict(X_test_rf)

# --- Inverte escala ---
def inverse_transform(scaled_values, scaled_full_data):
    full = np.zeros((len(scaled_values), scaled_full_data.shape[1]))
    full[:, 0] = scaled_values
    return scaler.inverse_transform(full)[:, 0]

pred_lstm = inverse_transform(pred_lstm_scaled, scaled_data)
pred_rf = inverse_transform(pred_rf_scaled, scaled_data)
real = inverse_transform(y_test_lstm, scaled_data)

# --- Métricas ---
def calc_metrics(true, pred, name):
    rmse = np.sqrt(mean_squared_error(true, pred))
    mae = mean_absolute_error(true, pred)
    print(f"{name} - RMSE: {rmse:.3f}, MAE: {mae:.3f}")
    return rmse, mae

rmse_lstm, mae_lstm = calc_metrics(real, pred_lstm, "LSTM")
rmse_rf, mae_rf = calc_metrics(real, pred_rf, "Random Forest")

# --- Gráfico comparativo ---
plt.figure(figsize=(14,7))
plt.plot(real, label='Preço Real', color='black')
plt.plot(pred_lstm, label='LSTM Previsto', color='blue')
plt.plot(pred_rf, label='Random Forest Previsto', color='green')
plt.title(f'Comparativo Previsão de Preço - {COIN}')
plt.xlabel('Tempo')
plt.ylabel('Preço em USD')
plt.legend()
plt.tight_layout()
plt.savefig("comparativo_previsao.png")
