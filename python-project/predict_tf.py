import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Carregar e validar dados
initial_df = pd.read_csv("data/dataset.csv")
if initial_df.empty:
    raise ValueError("Dataset está vazio.")

# Preprocessing (limpeza e preparação)
initial_df.dropna(axis=1, inplace=False)
initial_df = initial_df.loc[:, ~(initial_df == 0).any()]
initial_df.drop_duplicates(inplace=False)
initial_df.to_csv("data/dataset_clean.csv")

# Seleção de features e targets
df_full = pd.read_csv("data/dataset_clean.csv")
df = df_full.iloc[:-1]
last_row = df_full.iloc[-1:]

# Criação das features de tempo
df['data'] = pd.to_datetime(df[['year', 'month', 'day']])
df['dia_do_ano'] = df['data'].dt.dayofyear
df['dia_da_semana'] = df['data'].dt.weekday
df['semana'] = df['data'].dt.isocalendar().week.astype(int)
df['fim_de_semana'] = df['dia_da_semana'].isin([5, 6]).astype(int)

required_cols = ['fear_api_alternative_me', 'fear_coinmarketcap']
features = [
    'dia_do_ano', 'dia_da_semana', 'semana', 'fim_de_semana'
] + required_cols
X = df[features]

target_columns = [col for col in df.columns if col.endswith(
    '_min_value') or col.endswith('_max_value')]
y = df[target_columns]

# Normalização
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Divisão treino/teste
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42)

# Construção do modelo TensorFlow
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_dim=X_train.shape[1]),
    tf.keras.layers.Dropout(0.2),  # Regularização para evitar overfitting
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(len(target_columns))
])

model.compile(optimizer='adam', loss='mean_squared_error')

# Treinamento do modelo
model.fit(X_train, y_train, epochs=100, batch_size=8, verbose=1)

# Avaliação
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"\n\nErro quadrático médio no conjunto de teste: {mse:.4f}\n\n")

# Previsão para o próximo dia
nova_data = pd.Timestamp.today()
dia_do_ano = nova_data.dayofyear
dia_da_semana = nova_data.weekday()
semana = nova_data.isocalendar().week
fim_de_semana = 1 if dia_da_semana >= 5 else 0
fear_api_alternative_me = int(last_row['fear_api_alternative_me'].iloc[0])
fear_coinmarketcap = int(last_row['fear_coinmarketcap'].iloc[0])

# Criar array de features
predict_features = [[
    dia_do_ano,
    dia_da_semana,
    semana,
    fim_de_semana,
    fear_api_alternative_me,
    fear_coinmarketcap
]]
predict_scaled = scaler.transform(predict_features)
previsao = model.predict(predict_scaled)

# Resultado
predict_dictionary = dict(zip(target_columns, previsao[0]))
df_predict = pd.DataFrame([predict_dictionary])
df_predict.to_csv("data/predict.csv", index=False)
