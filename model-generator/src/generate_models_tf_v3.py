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

LOOK_BACK = 60
REQUIRED_FEAR_COLUMNS = ['fear_api_alternative_me', 'fear_coinmarketcap']


def create_sequences(data_X, data_y, look_back=60):
    X, y = [], []
    for i in range(len(data_X) - look_back):
        X.append(data_X[i:(i + look_back), :])
        y.append(data_y[i + look_back, :])
    return np.array(X), np.array(y)


def load_and_prepare_data():
    df = pd.read_csv(f"{DATA_PATH}/dataset_full.csv")
    if df.empty:
        raise ValueError("O dataset está vazio.")

    df.sort_values('OpenTime', inplace=True)

    percent_cols = []
    for col in df.columns:
        if not col.endswith('Close'):
            continue
        coin = col.replace('Close', '')
        for i in range(1, 5):
            prev = df[col].shift(i)
            new_col = ((df[col] - prev) / prev.replace(0, np.nan)) * 100
            percent_cols.append(new_col.rename(f'{coin}T{i}_percent'))

    df = pd.concat([df] + percent_cols, axis=1)

    missing = [col for col in REQUIRED_FEAR_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas de medo não encontradas: {missing}")

    return df


def extract_coin_names(df):
    price_columns = [col for col in df.columns if col.endswith(('High', 'Low'))]
    coins = sorted(list(set(col.replace('High', '').replace('Low', '') for col in price_columns)))
    return [c for c in coins if c]


def train_model_for_coin(df, coin):
    print(f"\n--- Treinando modelo para {coin} ---")

    target_cols = [f"{coin}High", f"{coin}Low"]
    if any(col not in df.columns for col in target_cols):
        print(f"Colunas alvo ausentes para {coin}. Pulando.")
        return None, None

    input_cols = [col for col in df.columns if col.endswith('High') or col.endswith('Low') or '_percent' in col]
    input_cols.extend(REQUIRED_FEAR_COLUMNS)

    df_clean = df[input_cols + target_cols].dropna()
    if len(df_clean) < LOOK_BACK + 1:
        print(f"Dados insuficientes para {coin} mesmo após limpeza. Pulando.")
        return None, None

    X_data = df_clean[input_cols].values
    y_data = df_clean[target_cols].values

    X_scaler = StandardScaler()
    y_scaler = StandardScaler()

    X_scaled = X_scaler.fit_transform(X_data)
    y_scaled = y_scaler.fit_transform(y_data)

    train_size = int(len(df_clean) * 0.8)
    X_train, X_test = X_scaled[:train_size], X_scaled[train_size:]
    y_train, y_test = y_scaled[:train_size], y_scaled[train_size:]

    X_train_seq, y_train_seq = create_sequences(X_train, y_train, LOOK_BACK)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, LOOK_BACK)

    if len(X_train_seq) == 0 or len(X_test_seq) == 0:
        print(f"Sequências insuficientes para {coin}. Pulando.")
        return None, None

    model = tf.keras.Sequential([
        tf.keras.Input(shape=(LOOK_BACK, X_train_seq.shape[2])),
        tf.keras.layers.LSTM(50, return_sequences=True),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(50),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(25, activation='relu'),
        tf.keras.layers.Dense(y_train_seq.shape[1])
    ])

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7)
    ]

    history = model.fit(
        X_train_seq, y_train_seq,
        epochs=50,
        batch_size=32,
        validation_data=(X_test_seq, y_test_seq),
        callbacks=callbacks,
        verbose=1
    )

    model_dir = f"{DATA_PATH}/models/lstm"
    os.makedirs(model_dir, exist_ok=True)

    model.save(f"{model_dir}/{coin}.keras")
    joblib.dump(X_scaler, f"{model_dir}/{coin}_x_scaler.save")
    joblib.dump(y_scaler, f"{model_dir}/{coin}_y_scaler.save")
    pd.DataFrame(history.history).to_csv(f"{model_dir}/{coin}_history.csv", index=False)

    y_pred_scaled = model.predict(X_test_seq, verbose=0)
    y_pred = y_scaler.inverse_transform(y_pred_scaled)
    y_test_orig = y_scaler.inverse_transform(y_test_seq)

    mse = mean_squared_error(y_test_orig, y_pred)
    pd.DataFrame({'Metric': ['MSE'], 'Value': [mse]}).to_csv(
        f"{model_dir}/{coin}_mse.csv", index=False)

    print(f"MSE (LSTM) para {coin}: {mse:.6f}")
    return coin, mse


def main():
    df = load_and_prepare_data()
    coins = extract_coin_names(df)
    print(f"Moedas encontradas: {coins}")

    results = {}
    for coin in coins:
        try:
            coin_name, mse = train_model_for_coin(df, coin)
            if coin_name:
                results[coin_name] = mse
        except Exception as e:
            print(f"Erro ao treinar {coin}: {e}")

    if results:
        results_df = pd.DataFrame(list(results.items()), columns=['Coin', 'MSE'])
        results_df.to_csv(f"{DATA_PATH}/models/lstm/lstm_model_evaluation_mse.csv", index=False)
        print("\nResumo dos resultados:")
        print(results_df)
    else:
        print("Nenhum modelo foi treinado com sucesso.")


if __name__ == "__main__":
    main()
