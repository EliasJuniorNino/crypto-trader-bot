import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import os
import joblib
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.getenv("DATA_DIR")

# --- Função para criar janelas temporais (sequências) ---

def create_sequences(data_X, data_y, look_back=60):
    X, y = [], []
    for i in range(len(data_X) - look_back):
        X.append(data_X[i:(i + look_back), :])
        y.append(data_y[i + look_back, :])
    return np.array(X), np.array(y)


# --- Carregar dados ---
try:
    df = pd.read_csv(f"{DATA_PATH}/datasets/dataset_full.csv")
except FileNotFoundError:
    raise FileNotFoundError("Arquivo 'data/dataset_full.csv' não encontrado.")

if df.empty:
    raise ValueError("O dataset está vazio.")

if 'fear_api_alternative_me' not in df.columns:
    raise ValueError(
        "Coluna 'fear_api_alternative_me' não encontrada no dataset.")

if 'fear_coinmarketcap' not in df.columns:
    raise ValueError(
        "Coluna 'fear_api_alternative_me' não encontrada no dataset.")

# --- Preparação ---
os.makedirs(f"{DATA_PATH}/models/lstm", exist_ok=True)

price_columns = [col for col in df.columns if col.endswith(('High', 'Low'))]
coins = sorted(list(set(col.replace('High', '').replace('Low', '')
               for col in price_columns)))
results = {}

print(f"Moedas encontradas: {coins}")

LOOK_BACK = 60

# --- Loop de treino por moeda ---
for coin in coins:
    print(f"\n--- Treinando modelo para {coin} ---")

    # --- Features de entrada: todas as colunas High/Low ---
    input_cols = [col for col in df.columns if col.endswith(('High', 'Low'))]
    input_cols.append('fear_api_alternative_me')
    input_cols.append('fear_coinmarketcap')

    target_cols = [f"{coin}High", f"{coin}Low"]
    if not all(col in df.columns for col in target_cols):
        print(f"Aviso: Colunas {target_cols} não encontradas. Pulando {coin}.")
        continue

    X_scaler = StandardScaler()
    X_scaled = X_scaler.fit_transform(df[input_cols])  # Entrada multivariada

    y_scaler = StandardScaler()
    y_scaled = y_scaler.fit_transform(df[target_cols].values)

    # Divisão temporal (sem embaralhar)
    train_size = int(len(df) * 0.8)
    X_train = X_scaled[:train_size]
    X_test = X_scaled[train_size:]
    y_train = y_scaled[:train_size]
    y_test = y_scaled[train_size:]

    # Criar sequências
    X_train_seq, y_train_seq = create_sequences(X_train, y_train, LOOK_BACK)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, LOOK_BACK)

    if X_train_seq.shape[0] == 0 or X_test_seq.shape[0] == 0:
        print(f"Dados insuficientes para {coin}. Pulando.")
        continue

    print(f"Formato de X_train: {X_train_seq.shape}")
    print(f"Formato de y_train: {y_train_seq.shape}")

    # --- Modelo LSTM ---
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, return_sequences=True,
                             input_shape=(LOOK_BACK, X_train_seq.shape[2])),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(25),
        tf.keras.layers.Dense(y_train_seq.shape[1])  # saída: High e Low
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    # --- Treinar ---
    model.fit(
        X_train_seq, y_train_seq,
        epochs=20,
        batch_size=64,
        validation_data=(X_test_seq, y_test_seq),
        verbose=1
    )
    print("Treinamento concluído.")

    # Salvar modelo
    model_path = f"{DATA_PATH}/models/lstm/{coin}.keras"
    model.save(model_path)

    # Salvar scaler
    joblib.dump(X_scaler, f"{DATA_PATH}/models/lstm/{coin}_x_scaler.save")
    joblib.dump(y_scaler, f"{DATA_PATH}/models/lstm/{coin}_y_scaler.save")

    # --- Avaliar ---
    y_pred_scaled = model.predict(X_test_seq)
    y_pred = y_scaler.inverse_transform(y_pred_scaled)
    y_test_orig = y_scaler.inverse_transform(y_test_seq)

    mse = mean_squared_error(y_test_orig, y_pred)
    results[coin] = mse
    print(f"MSE (LSTM) para {coin}: {mse}")

    # --- Salvar MSE por moeda ---
    coin_result_df = pd.DataFrame({
        'Metric': ['MSE'],
        'Value': [mse]
    })
    coin_result_df.to_csv(f"{DATA_PATH}/models/lstm/{coin}_mse.csv", index=False)

# --- Salvar resumo geral ---
results_df = pd.DataFrame(list(results.items()), columns=['Coin', 'MSE'])
results_df.to_csv(f"{DATA_PATH}/models/lstm/lstm_model_evaluation_mse.csv", index=False)
print("\nTodos os MSEs salvos em 'models/lstm/lstm_model_evaluation_mse.csv'")
