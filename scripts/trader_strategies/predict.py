import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.feature_selection import SelectKBest, f_regression

# 1. Carregar dados
df = pd.read_csv("data/dataset.csv")
if df.empty:
    raise ValueError("Dataset está vazio.")

# 2. Limpeza
df.dropna(axis=1, inplace=True)
df = df.loc[:, ~(df == 0).any()]
df.drop_duplicates(inplace=True)

# 3. Dividir dados: última linha para previsão, resto para treino
df_data = df.iloc[:-1]
last_row = df.iloc[-1:]

# 4. Criar features temporais
df_data['data'] = pd.to_datetime(df_data[['year', 'month', 'day']])
df_data['dia_do_ano'] = df_data['data'].dt.dayofyear
df_data['dia_da_semana'] = df_data['data'].dt.weekday
df_data['semana'] = df_data['data'].dt.isocalendar().week.astype(int)
df_data['fim_de_semana'] = df_data['dia_da_semana'].isin([5, 6]).astype(int)

# 5. Definir targets e features
target_columns = [col for col in df_data.columns if col.endswith('_min_value') or col.endswith('_max_value')]
non_feature_cols = ['year', 'month', 'day', 'data'] + target_columns
X = df_data.drop(columns=non_feature_cols)
y = df_data[target_columns]

# 6. Normalização
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 7. Seleção das K melhores features (ex: 15)
selector = SelectKBest(score_func=f_regression, k=15)
X_selected = selector.fit_transform(X_scaled, y['ETH_min_value'])  # usa uma das colunas para selecionar features

# Opcional: manter apenas as colunas selecionadas
selected_feature_indices = selector.get_support(indices=True)
X = X.iloc[:, selected_feature_indices]
X_scaled = scaler.fit_transform(X)

# 8. Treino/teste
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 9. Treinar Random Forest
modelo = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
modelo.fit(X_train, y_train)

# 10. Avaliação
y_pred = modelo.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"\nErro quadrático médio: {mse:.4f}")

# 11. Previsão com última linha
last_row['data'] = pd.to_datetime(last_row[['year', 'month', 'day']])
last_row['dia_do_ano'] = last_row['data'].dt.dayofyear
last_row['dia_da_semana'] = last_row['data'].dt.weekday
last_row['semana'] = last_row['data'].dt.isocalendar().week.astype(int)
last_row['fim_de_semana'] = last_row['dia_da_semana'].isin([5, 6]).astype(int)

# Selecionar e preparar as features da última linha
X_last = last_row[X.columns]
X_last_scaled = scaler.transform(X_last)

# Previsão
previsao = modelo.predict(X_last_scaled)
predict_dict = dict(zip(target_columns, previsao[0]))
df_predict = pd.DataFrame([predict_dict])
df_predict.to_csv("data/predict.csv", index=False)
