import os
import time
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
df = df[-(1440*30):]

# Encontrar colunas de preços
price_columns = [col for col in df.columns if col.endswith(('_PercentHigh', '_PercentLow'))]
if not price_columns:
    raise ValueError("Nenhuma coluna de preços (_PercentHigh/_PercentLow) encontrada no dataset.")

coins = sorted(list(set(col.replace('_PercentHigh', '').replace('_PercentLow', '') for col in price_columns)))
coins = [coin for coin in coins if coin]  # Remove strings vazias

df['OpenTime'] = pd.to_datetime(df['OpenTime'])
df.set_index('OpenTime', inplace=True)

features = ['fear_api_alternative_me', 'fear_coinmarketcap']
for coin in coins:
    features.append(f"{coin}_PercentHigh")
    features.append(f"{coin}_PercentLow")
df = df[features]

# --- Normaliza dados ---
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df)

def create_sequences_lstm(data, target_indices, look_back=30):
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i])  # shape (look_back, num_features)
        y.append(data[i, target_indices])  # previsão para o timestep atual
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

for coin in coins:
    LOOK_BACK = 60

    # Divisão treino/teste
    split_idx = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:split_idx]
    test_data = scaled_data[split_idx - LOOK_BACK:]

    high_col = f"{coin}_PercentHigh"
    low_col = f"{coin}_PercentLow"
    target_indices = [df.columns.get_loc(high_col), df.columns.get_loc(low_col)]

    X_train, y_train = create_sequences_lstm(train_data, target_indices, LOOK_BACK)
    X_test, y_test = create_sequences_lstm(test_data, target_indices, LOOK_BACK)

    # --- Modelo LSTM com Dropout e mais unidades ---
    model = Sequential([
      Input(shape=(LOOK_BACK, len(features))),
      LSTM(128, return_sequences=False),
      Dropout(0.2),
      Dense(64, activation='relu'),
      Dropout(0.2),
      Dense(2)  # previsão para PercentHigh e PercentLow
    ])

    model.compile(optimizer='adam', loss='mse')
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

    model.fit(
        X_train, y_train,
        validation_split=0.1,
        epochs=25,
        batch_size=64,
        callbacks=[early_stop],
        verbose=2
    )

    # --- Previsão ---
    pred_scaled = model.predict(X_test)

    # --- Inverter escala ---
    def inverse_transform_lstm(scaled_values, scaled_full_data, indices):
        full = np.zeros((len(scaled_values), scaled_full_data.shape[1]))
        for i, idx in enumerate(indices):
            full[:, idx] = scaled_values[:, i]
        inversed = scaler.inverse_transform(full)
        return inversed[:, indices]

    pred = inverse_transform_lstm(pred_scaled, scaled_data, target_indices)
    real = inverse_transform_lstm(y_test, scaled_data, target_indices)

    # --- Métricas ---
    rmse_high = np.sqrt(mean_squared_error(real[:, 0], pred[:, 0]))
    mae_high = mean_absolute_error(real[:, 0], pred[:, 0])
    rmse_low = np.sqrt(mean_squared_error(real[:, 1], pred[:, 1]))
    mae_low = mean_absolute_error(real[:, 1], pred[:, 1])

    print(f"Coin: {coin}")
    print(f"RMSE PercentHigh: {rmse_high:.4f}, MAE PercentHigh: {mae_high:.4f}")
    print(f"RMSE PercentLow: {rmse_low:.4f}, MAE PercentLow: {mae_low:.4f}")

    # --- Salvar modelo ---
    model_dir = f"{DATASET_DIR}/models/lstm"
    os.makedirs(model_dir, exist_ok=True)
    model.save(f"{model_dir}/{coin}_lstm_model.keras")

    # --- Salvar métricas ---
    metrics_df = pd.DataFrame([{
        'coin': coin,
        'rmse_high': round(rmse_high, 4),
        'mae_high': round(mae_high, 4),
        'rmse_low': round(rmse_low, 4),
        'mae_low': round(mae_low, 4)
    }])
    metrics_df.to_csv(f"{model_dir}/{coin}_metrics.csv", index=False)

end_time = time.time()
total_time = end_time - start_time
print(f"\nTempo total de execução: {total_time:.2f} segundos ({total_time / 60:.2f} minutos)")
