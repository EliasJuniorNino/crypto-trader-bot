import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Carregar e validar dados
df = pd.read_csv("data/dataset_full.csv")
if df.empty:
    raise ValueError("Dataset está vazio.")

df_columns = [col for col in df.columns
              if col.endswith('High') or col.endswith('Low')]

coins = [col.replace('High', '') for col in df_columns if col.endswith('High')]
for coin in coins:
    features = [col for col in df_columns if not col.startswith(coin)]
    X = df[features]

    target_columns = [col for col in df_columns if col.startswith(coin)]
    y = df[target_columns]

    # Normalização dos dados de entrada (X)
    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)

    # Normalização dos dados de saída (y)
    scaler_y = StandardScaler()
    y_scaled = scaler_y.fit_transform(y)

    # Divisão treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_scaled, test_size=0.2, random_state=42)

    # Construção do modelo TensorFlow
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu',
                              input_dim=X_train.shape[1]),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation='relu'),
        # output igual ao número de colunas de y
        tf.keras.layers.Dense(y.shape[1])
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    # Treinamento do modelo
    model.fit(X_train, y_train, epochs=100,
              batch_size=X_train.shape[0], verbose=1)
    model.save(f"data/models/{coin}.keras")

    # Predição
    y_pred_scaled = model.predict(X_test)

    # Desnormalizar as saídas
    y_pred = scaler_y.inverse_transform(y_pred_scaled)
    y_test_original = scaler_y.inverse_transform(y_test)

    # Avaliação
    mse = mean_squared_error(y_test_original, y_pred)
    with open(f"data/models/{coin}.txt", "w") as f:
        f.write(f"{mse:.30f}\n")
