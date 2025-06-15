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
    df = pd.read_csv(f"{DATA_PATH}/dataset_full.csv")
except FileNotFoundError:
    raise FileNotFoundError(f"Arquivo {DATA_PATH}/data/dataset_full.csv, não encontrado.")

if df.empty:
    raise ValueError("O dataset está vazio.")

# Ordena dataset por data
df.sort_values('OpenTime', inplace=True)

# Gera colunas temporais
percent_cols = []
for col in df.columns:
    if not col.endswith('Close'):
        continue
    coin = col.replace('Close', '')
    for i in range(1, 5):
        prev = df[col].shift(i)
        new_col = ((df[col] - prev) / prev.replace(0, np.nan)) * 100
        percent_cols.append(new_col.rename(f'{coin}T{i}_percent'))

# Concatena todas de uma vez
df = pd.concat([df] + percent_cols, axis=1)

# Verificar se as colunas de medo existem
required_fear_columns = ['fear_api_alternative_me', 'fear_coinmarketcap']
missing_fear_columns = [
    col for col in required_fear_columns if col not in df.columns]
if missing_fear_columns:
    raise ValueError(f"Colunas de medo não encontradas no dataset: {missing_fear_columns}")

# --- Preparação ---
os.makedirs(f"{DATA_PATH}/models/lstm", exist_ok=True)

# Encontrar colunas de preços
price_columns = [col for col in df.columns if col.endswith(('High', 'Low'))]
if not price_columns:
    raise ValueError("Nenhuma coluna de preços (High/Low) encontrada no dataset.")

# Extrair nomes das moedas
coins = sorted(list(set(col.replace('High', '').replace('Low', '') for col in price_columns)))
coins = [coin for coin in coins if coin]  # Remove strings vazias

results = {}

print(f"Moedas encontradas: {coins}")

LOOK_BACK = 60

# --- Loop de treino por moeda ---
for coin in coins[:10]:
    print(f"\n--- Treinando modelo para {coin} ---")

    # Verificar se as colunas alvo existem
    target_cols = [f"{coin}High", f"{coin}Low"]
    missing_target_cols = [col for col in target_cols if col not in df.columns]
    if missing_target_cols:
        print(f"Aviso: Colunas {missing_target_cols} não encontradas. Pulando {coin}.")
        continue

    # --- Features de entrada: todas as colunas High/Low + indicadores de medo ---
    input_cols = [col for col in df.columns if col.endswith('High') or col.endswith('Low') or '_percent' in col]
    input_cols.extend(required_fear_columns)

    # Verificar se há dados suficientes
    if len(df) < LOOK_BACK + 1:
        print(f"Dados insuficientes (menos que {LOOK_BACK + 1} registros). Pulando {coin}.")
        continue

    # Verificar valores NaN e tratar
    df_clean = df[input_cols + target_cols].dropna()
    if len(df_clean) < LOOK_BACK + 1:
        print(f"Dados insuficientes após remoção de NaN para {coin}. Pulando.")
        continue

    # Preparar dados
    X_data = df_clean[input_cols].values
    y_data = df_clean[target_cols].values

    # Normalização
    X_scaler = StandardScaler()
    X_scaled = X_scaler.fit_transform(X_data)

    y_scaler = StandardScaler()
    y_scaled = y_scaler.fit_transform(y_data)

    # Divisão temporal (sem embaralhar)
    train_size = int(len(df_clean) * 0.8)
    X_train = X_scaled[:train_size]
    X_test = X_scaled[train_size:]
    y_train = y_scaled[:train_size]
    y_test = y_scaled[train_size:]

    # Criar sequências
    X_train_seq, y_train_seq = create_sequences(X_train, y_train, LOOK_BACK)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, LOOK_BACK)

    if X_train_seq.shape[0] == 0 or X_test_seq.shape[0] == 0:
        print(f"Dados insuficientes para criar sequências para {coin}. Pulando.")
        continue

    print(f"Formato de X_train: {X_train_seq.shape}")
    print(f"Formato de y_train: {y_train_seq.shape}")

    # --- Modelo LSTM ---
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(LOOK_BACK, X_train_seq.shape[2])),
        tf.keras.layers.LSTM(50, return_sequences=True),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(25, activation='relu'),
        tf.keras.layers.Dense(y_train_seq.shape[1])  # saída: High e Low
    ])

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

    # Callbacks para melhorar o treinamento
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=5, restore_best_weights=True
    )

    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7
    )

    # --- Treinar ---
    try:
        history = model.fit(
            X_train_seq, y_train_seq,
            epochs=50,
            batch_size=32,
            validation_data=(X_test_seq, y_test_seq),
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        print("Treinamento concluído.")

        # Salvar modelo
        model_path = f"{DATA_PATH}/models/lstm/{coin}.keras"
        model.save(model_path)

        # Salvar scalers
        joblib.dump(X_scaler, f"{DATA_PATH}/models/lstm/{coin}_x_scaler.save")
        joblib.dump(y_scaler, f"{DATA_PATH}/models/lstm/{coin}_y_scaler.save")

        # --- Avaliar ---
        y_pred_scaled = model.predict(X_test_seq, verbose=0)
        y_pred = y_scaler.inverse_transform(y_pred_scaled)
        y_test_orig = y_scaler.inverse_transform(y_test_seq)

        mse = mean_squared_error(y_test_orig, y_pred)
        results[coin] = mse
        print(f"MSE (LSTM) para {coin}: {mse:.6f}")

        # --- Salvar MSE por moeda ---
        coin_result_df = pd.DataFrame({
            'Metric': ['MSE'],
            'Value': [mse]
        })
        coin_result_df.to_csv(f"{DATA_PATH}/models/lstm/{coin}_mse.csv", index=False)

    except Exception as e:
        print(f"Erro durante o treinamento para {coin}: {str(e)}")
        continue

# --- Salvar resumo geral ---
if results:
    results_df = pd.DataFrame(list(results.items()), columns=['Coin', 'MSE'])
    results_df.to_csv(f"{DATA_PATH}/models/lstm/lstm_model_evaluation_mse.csv", index=False)
    print(f"\nResumo dos resultados:")
    print(results_df)
    print(f"\nTodos os MSEs salvos em {DATA_PATH}/lstm_model_evaluation_mse.csv'")
else:
    print("Nenhum modelo foi treinado com sucesso.")
