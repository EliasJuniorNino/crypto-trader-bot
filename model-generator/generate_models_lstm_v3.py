import os
import time
import gc
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

start_time = time.time()

print("GPU disponível:", tf.config.list_physical_devices('GPU'))

# --- Variáveis de ambiente ---
load_dotenv()
DATASET_DIR = os.getenv("DATASET_DIR")

# --- Carrega dados ---
df = pd.read_csv(f"{DATASET_DIR}/dataset_percent.csv")
df['OpenTime'] = pd.to_datetime(df['OpenTime'])
df.set_index('OpenTime', inplace=True)

# --- Identifica colunas ---
price_columns = [col for col in df.columns if col.endswith(('_PercentHigh', '_PercentLow'))]
coins = sorted(list(set(col.replace('_PercentHigh', '').replace('_PercentLow', '') for col in price_columns)))
coins = [coin for coin in coins if coin]

features = ['fear_api_alternative_me', 'fear_coinmarketcap']
for coin in coins:
    features.extend([f"{coin}_PercentHigh", f"{coin}_PercentLow"])

df = df[features]
df.dropna(inplace=True)

# --- Parâmetros ---
BLOCK_DAYS = 7
INTERVALS_PER_DAY = 1440
LOOK_BACK = 60

# --- Funções auxiliares ---
def split_by_days(df, block_days, interval_per_day=1440):
    total_intervals = block_days * interval_per_day
    num_blocks = len(df) // total_intervals
    return [df[i*total_intervals:(i+1)*total_intervals] for i in range(num_blocks)]

def create_sequences_lstm(data, target_indices, look_back=60):
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i])
        y.append(data[i, target_indices])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def inverse_transform_lstm(scaled_values, scaled_full_data, indices, scaler):
    full = np.zeros((len(scaled_values), scaled_full_data.shape[1]))
    for i, idx in enumerate(indices):
        full[:, idx] = scaled_values[:, i]
    inversed = scaler.inverse_transform(full)
    return inversed[:, indices]

# --- Processamento por blocos com aprendizado incremental ---
blocks = split_by_days(df, BLOCK_DAYS, INTERVALS_PER_DAY)
all_metrics = []
model = None  # modelo global para fine-tuning entre blocos

for i, block_df in enumerate(blocks):
    print(f"\n🔁 Processando bloco {i+1}/{len(blocks)}...")

    block_df.dropna(inplace=True)
    if block_df.empty or len(block_df) < LOOK_BACK + 1:
        print(f"  ⚠️ Bloco {i+1} ignorado (dados insuficientes)")
        continue

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(block_df)

    target_indices = [block_df.columns.get_loc(f"{coin}_{suffix}") for coin in coins for suffix in ("PercentHigh", "PercentLow")]

    split_idx = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:split_idx]
    test_data = scaled_data[split_idx - LOOK_BACK:]

    X_train, y_train = create_sequences_lstm(train_data, target_indices, LOOK_BACK)
    X_test, y_test = create_sequences_lstm(test_data, target_indices, LOOK_BACK)

    if model is None:
        model = Sequential([
            Input(shape=(LOOK_BACK, len(features))),
            LSTM(128, return_sequences=False),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(len(target_indices))
        ])
        model.compile(optimizer='adam', loss='mse')

    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    model.fit(X_train, y_train, validation_split=0.1, epochs=100, batch_size=128, callbacks=[early_stop], verbose=2)

    pred_scaled = model.predict(X_test)
    pred = inverse_transform_lstm(pred_scaled, scaled_data, target_indices, scaler)
    real = inverse_transform_lstm(y_test, scaled_data, target_indices, scaler)

    if np.isnan(pred).any() or np.isnan(real).any():
        print(f"  ⚠️ Bloco {i+1} contém valores NaN após inversão. Ignorado.")
        continue

    for j, coin in enumerate(coins):
        idx_high = j * 2
        idx_low = idx_high + 1

        rmse_high = np.sqrt(mean_squared_error(real[:, idx_high], pred[:, idx_high]))
        mae_high = mean_absolute_error(real[:, idx_high], pred[:, idx_high])
        rmse_low = np.sqrt(mean_squared_error(real[:, idx_low], pred[:, idx_low]))
        mae_low = mean_absolute_error(real[:, idx_low], pred[:, idx_low])

        print(f"  Coin: {coin} | Block: {i+1}")
        print(f"    RMSE High: {rmse_high:.4f}, MAE High: {mae_high:.4f}")
        print(f"    RMSE Low:  {rmse_low:.4f}, MAE Low:  {mae_low:.4f}")

        all_metrics.append({
            'block': i+1,
            'coin': coin,
            'rmse_high': round(rmse_high, 4),
            'mae_high': round(mae_high, 4),
            'rmse_low': round(rmse_low, 4),
            'mae_low': round(mae_low, 4)
        })

    # modelo é mantido e refinado no próximo bloco (fine-tuning)
    gc.collect()

# --- Salva resultados ---
model_dir = f"{DATASET_DIR}/models/lstm_multicoin_incremental"
os.makedirs(model_dir, exist_ok=True)

metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(f"{model_dir}/metrics_all_blocks.csv", index=False)

end_time = time.time()
total_time = end_time - start_time
print(f"\nTempo total de execução: {total_time:.2f} segundos ({total_time / 60:.2f} minutos)")
