import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from model.database import connect_db


# Train model
def train_model(df, column_index):
    # Separando X (features) e y (targets)
    X = df.drop(columns=[f"col_{column_index}", f"col_{column_index + 1}"])  # Variáveis de entrada
    y = df[[f"col_{column_index}", f"col_{column_index + 1}"]]  # Valores a serem previstos

    # Normalizando os dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Dividindo os dados em treino (80%) e teste (20%)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Criando o modelo
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Fazendo previsões
    y_pred = model.predict(X_test)

    # Avaliando o modelo
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"MAE: {mae:.6f}")
    print(f"RMSE: {rmse:.6f}")

    return model, scaler


def get_data(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT *
        FROM fear_greed_index
        ORDER BY timestamp DESC
        LIMIT 6
    """)
    data = []
    for (fear_id, fear_timestamp, fear_value, fear_class) in cursor.fetchall():
        date_interval = (fear_timestamp, fear_timestamp + timedelta(days=1))
        cursor.execute("""
            SELECT coin,
                   MAX(price) AS max_price,
                   MIN(price) AS min_price
            FROM coin_price_history
            WHERE date BETWEEN %s AND %s
            GROUP BY coin
        """, date_interval)
        crypto_values = [fear_timestamp, fear_value]
        for (coin, max_price, min_price) in cursor.fetchall():
            crypto_values.append(max_price)
            crypto_values.append(min_price)
        if not len(crypto_values) in [2]:
            data.append(crypto_values)
            print('crypto_values', crypto_values, end='\n')

    max_columns = max(len(row) for row in data)

    # Criando nomes de colunas dinamicamente
    column_names = [f"col_{i}" for i in range(max_columns)]

    # Padronizando o tamanho das linhas (preenchendo com None ou 0 se necessário)
    data_padded = [row + [None] * (max_columns - len(row)) for row in data]

    # Criando o DataFrame
    df = pd.DataFrame(data_padded, columns=column_names)

    # Convertendo a coluna 'date' para datetime
    df["col_0"] = pd.to_datetime(df["col_0"])

    # Extraindo features da data
    df["year"] = df["col_0"].dt.year
    df["month"] = df["col_0"].dt.month
    df["day"] = df["col_0"].dt.day
    df["day_of_week"] = df["col_0"].dt.weekday
    df["timestamp"] = df["col_0"].astype("int64") // 10 ** 9

    # Removendo a coluna original 'date'
    df.drop(columns=["col_0"], inplace=True)

    for i in range(2, max_columns):
        model, scaler = train_model(df.copy(), i)

        # Fazendo uma previsão para um novo exemplo
        # Criar DataFrame de teste sem a coluna alvo
        df_test = df.copy().drop(columns=[f"col_{i}", f"col_{i + 1}"])

        # Preparar novo dado para previsão
        novo_dado = np.array([0 if v is None else v for v in df_test.iloc[0]]).reshape(1, -1)
        novo_dado_scaled = scaler.transform(novo_dado)

        # Fazer a previsão usando o modelo treinado
        previsao = model.predict(novo_dado_scaled)

        # Obter previsões individuais de cada árvore
        tree_predictions = np.array([tree.predict(novo_dado_scaled)[0] for tree in model.estimators_])

        # Calcular o desvio padrão das previsões
        confianca = np.std(tree_predictions)

        print(f"Previsão de preço: {previsao[0]}")
        print(f"Confiança da previsão: {confianca:.6f}")


# Executar o fluxo
if __name__ == "__main__":
    db_conn = connect_db()
    if db_conn:
        get_data(db_conn)
        db_conn.close()
