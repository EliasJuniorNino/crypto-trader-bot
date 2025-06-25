import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import json

# === 1) Ler dados ===
X = pd.read_csv("X_dataset_full.csv")
Y = pd.read_csv("Y_dataset_full.csv")

# === 2) Dividir treino/teste ===
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, shuffle=False)

# === 3) ----------- RANDOM FOREST MultiOutput -------------- ===
rf_base = RandomForestRegressor(n_estimators=100, random_state=42)
rf = MultiOutputRegressor(rf_base)
rf.fit(X_train, Y_train)

# Previsões
Y_pred_rf = rf.predict(X_test)

# Métricas RF
mse_rf = mean_squared_error(Y_test, Y_pred_rf)
r2_rf = r2_score(Y_test, Y_pred_rf)

print(f"[RandomForest] MSE: {mse_rf:.4f} | R2: {r2_rf:.4f}")

# Salvar modelo
joblib.dump(rf, "random_forest_multioutput_model.pkl")

# === 4) ----------- LSTM Multi-step -------------- ===

# Para LSTM multi-step:
# Entrada: [samples, timesteps, features]
# Saída: [samples, steps_ahead]

# Aqui: timesteps = 1 (por minuto), steps_ahead = 4

X_train_lstm = np.expand_dims(X_train.values, axis=1)
X_test_lstm = np.expand_dims(X_test.values, axis=1)

model = Sequential()
model.add(LSTM(64, activation='relu', input_shape=(1, X_train.shape[1])))
model.add(RepeatVector(4))  # 4 passos futuros
model.add(LSTM(64, activation='relu', return_sequences=True))
model.add(TimeDistributed(Dense(1)))  # Um valor por passo futuro

model.compile(optimizer='adam', loss='mse')

es = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train_lstm, Y_train.values.reshape((-1, 4, 1)),
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=[es],
    verbose=1
)

# Previsão LSTM
Y_pred_lstm = model.predict(X_test_lstm).squeeze()

# Ajustar shape se necessário
if len(Y_pred_lstm.shape) == 1:
    Y_pred_lstm = Y_pred_lstm.reshape(-1, 4)

# Métricas LSTM
mse_lstm = mean_squared_error(Y_test, Y_pred_lstm)
r2_lstm = r2_score(Y_test, Y_pred_lstm)

print(f"[LSTM] MSE: {mse_lstm:.4f} | R2: {r2_lstm:.4f}")

# Salvar modelo
model.save("lstm_multioutput_model.h5")

# === 5) Salvar métricas ===
metrics = {
    "RandomForest": {
        "MSE": mse_rf,
        "R2": r2_rf
    },
    "LSTM": {
        "MSE": mse_lstm,
        "R2": r2_lstm
    }
}

with open("metrics_multioutput.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("\nTodos os modelos multi-step e métricas foram salvos com sucesso.")
