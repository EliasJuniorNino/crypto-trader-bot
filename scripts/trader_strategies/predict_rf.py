import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

# Carregar e validar dados
initial_df = pd.read_csv("data/dataset.csv")
if initial_df.empty:
    raise ValueError("Dataset está vazio.")

# Preprocessing (limpeza e preparação)
initial_df.dropna(axis=1, inplace=True)
initial_df = initial_df.loc[:, ~((initial_df == 0) | (initial_df.isna())).any()]
initial_df.drop_duplicates(inplace=True)
initial_df.to_csv("data/dataset_clean.csv", index=False)

# Seleção de features e targets
df_full = pd.read_csv("data/dataset_clean.csv")
df = df_full.iloc[:-1]  # Remove a última linha (usada para previsão)
last_row = df_full.iloc[-1:]  # Última linha para previsão futura

# Criação das features de tempo
df['data'] = pd.to_datetime(df[['year', 'month', 'day']])
df['dia_do_ano'] = df['data'].dt.dayofyear
df['dia_da_semana'] = df['data'].dt.weekday
df['semana'] = df['data'].dt.isocalendar().week.astype(int)
df['fim_de_semana'] = df['dia_da_semana'].isin([5, 6]).astype(int)

# Colunas necessárias para o modelo
required_cols = ['fear_api_alternative_me', 'fear_coinmarketcap']
features = ['dia_do_ano', 'dia_da_semana', 'semana', 'fim_de_semana'] + required_cols
X = df[features]

# Detectando dinamicamente as colunas target (valores mínimos e máximos)
target_columns = [col for col in df.columns if col.endswith('_min_value') or col.endswith('_max_value')]
y = df[target_columns]

# Normalização dos dados de entrada
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Divisão em treino e teste (80% treino, 20% teste)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Criando o modelo Random Forest
modelo_rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)

# Treinando o modelo
modelo_rf.fit(X_train, y_train)

# Avaliação (erro quadrático médio)
y_pred = modelo_rf.predict(X_test)
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

# Criar array de features para previsão
predict_features = [[
    dia_do_ano,
    dia_da_semana,
    semana,
    fim_de_semana,
    fear_api_alternative_me,
    fear_coinmarketcap
]]
predict_scaled = scaler.transform(predict_features)

# Previsão para o próximo dia
previsao = modelo_rf.predict(predict_scaled)

# Resultado
predict_dictionary = dict(zip(target_columns, previsao[0]))
df_predict = pd.DataFrame([predict_dictionary])
df_predict.to_csv("data/predict.csv", index=False)
