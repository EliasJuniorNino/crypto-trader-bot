import os
import argparse
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras import Input

# --- Argumentos de linha de comando ---
parser = argparse.ArgumentParser(description="LSTM para prever preço de criptomoeda")
parser.add_argument('--coin', type=str, required=True, help='Símbolo da moeda, ex: BTC, ETH')
args = parser.parse_args()

COIN = args.coin.upper()

# --- Variáveis de ambiente ---
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR")

# --- Carrega os dados ---
df = pd.read_csv(f"{DATA_DIR}/dataset_full.csv")

# Verifica se a coluna da moeda existe
if f"{COIN}Close" not in df.columns:
    raise ValueError(f"Coluna {COIN}Close não encontrada no CSV. Verifique o nome da moeda.")

# Seleciona colunas
df = df[['OpenTime', f"{COIN}Close", 'fear_api_alternative_me', 'fear_coinmarketcap']]
df['OpenTime'] = pd.to_datetime(df['OpenTime'])
df.set_index('OpenTime', inplace=True)

# --- Normaliza os dados ---
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df)

# --- Cria sequências ---
LOOK_BACK = 60

def create_sequences(data, look_back=60):
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i])
        y.append(data[i, 0])  # Alvo = preço da moeda
    return np.array(X), np.array(y)

# --- Divide em treino e teste ---
split_index = int(len(scaled_data) * 0.8)
train_data = scaled_data[:split_index]
test_data = scaled_data[split_index - LOOK_BACK:]

X_train, y_train = create_sequences(train_data)
X_test, y_test = create_sequences(test_data)

# --- Modelo LSTM ---
model = Sequential([
    Input(shape=(X_train.shape[1], X_train.shape[2])),
    LSTM(50, return_sequences=True),
    Dropout(0.2),
    LSTM(50),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()

# --- Treinamento ---
history = model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.1)

# --- Salva o modelo ---
model_dir = f"{DATA_DIR}/modelos"
os.makedirs(model_dir, exist_ok=True)
model_path = f"{model_dir}/{COIN.lower()}_lstm_model.keras"
model.save(model_path)
print(f"Modelo salvo em {model_path}")

# --- Previsão ---
predicted_scaled = model.predict(X_test)

# Reconstrói para inversão
predicted_full = np.zeros((predicted_scaled.shape[0], scaled_data.shape[1]))
predicted_full[:, 0] = predicted_scaled[:, 0]

real_full = np.zeros((y_test.shape[0], scaled_data.shape[1]))
real_full[:, 0] = y_test

predicted_prices = scaler.inverse_transform(predicted_full)[:, 0]
real_prices = scaler.inverse_transform(real_full)[:, 0]

# --- Métricas ---
rmse = np.sqrt(mean_squared_error(real_prices, predicted_prices))
mae = mean_absolute_error(real_prices, predicted_prices)

print(f"RMSE ({COIN}): {rmse:.2f}")
print(f"MAE  ({COIN}): {mae:.2f}")

# --- Salva métricas em CSV ---
metrics_path = f"{DATA_DIR}/previsao/{COIN.lower()}_metrics.csv"
metrics_df = pd.DataFrame([{
    'coin': COIN,
    'rmse': round(rmse, 2),
    'mae': round(mae, 2)
}])
metrics_df.to_csv(metrics_path, index=False)
print(f"Métricas salvas em {metrics_path}")

# --- Gráfico ---
plt.figure(figsize=(12, 6))
plt.plot(real_prices, label=f'{COIN} Real', color='blue')
plt.plot(predicted_prices, label=f'{COIN} Previsto', color='red')
plt.title(f'Previsão de Preço do {COIN} - Conjunto de Teste')
plt.xlabel('Tempo')
plt.ylabel('Preço em USD')
plt.legend()
plt.tight_layout()
os.makedirs(f"{DATA_DIR}/previsao", exist_ok=True)
plt.savefig(f"{DATA_DIR}/previsao/{COIN.lower()}_preco_teste.png")
print(f"Gráfico salvo como {DATA_DIR}/previsao/{COIN.lower()}_preco_teste.png")
