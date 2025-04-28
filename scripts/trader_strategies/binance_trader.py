import subprocess
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# 1. Carregar dados
df = pd.read_csv("data/dataset.csv")

# 2. Remover colunas com valores NaN
df.dropna(axis=1, inplace=True)

# 3. Transformar data
df['data'] = pd.to_datetime(df[['year', 'month', 'day']])
df['dia_do_ano'] = df['data'].dt.dayofyear

# 4. Criar as features e targets
X = df[['dia_do_ano', 'fear_api_alternative_me', 'fear_coinmarketcap']]  # Features

# Detectar dinamicamente colunas de target
target_columns = [col for col in df.columns if col.endswith('_min_value') or col.endswith('_max_value')]
y = df[target_columns]

# 5. Treinar modelo
modelo = RandomForestRegressor(n_estimators=100, random_state=42)
modelo.fit(X, y)

# 6. Prever para o próximo dia (exemplo: 2025-02-04)
nova_data = pd.Timestamp("2025-04-23")
dia_do_ano = nova_data.dayofyear
fear_api_alternative_me = 72
fear_coinmarketcap = 52

predict_features = [dia_do_ano, fear_api_alternative_me, fear_coinmarketcap]
previsao = modelo.predict([predict_features])
full_predict = np.concatenate([np.array(predict_features), np.array(previsao[0])])

# 7. Exibir resultado
predict_dictionary = dict(zip(target_columns, previsao[0]))
print(predict_dictionary['ETH_min_value'])
print(predict_dictionary['ETH_max_value'])
