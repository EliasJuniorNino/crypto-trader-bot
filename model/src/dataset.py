from mysql.connector import Error
import pandas as pd
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_data(db_connection):
    """Busca os dados do banco de dados e retorna um DataFrame."""
    try:
        cursor = db_connection.cursor()

        # Busca os símbolos das moedas
        cursor.execute("SELECT symbol FROM binance_cryptos_names GROUP BY symbol")
        coin_names = [row[0] for row in cursor.fetchall()]

        # Busca os dados do índice de medo e ganância
        cursor.execute("SELECT * FROM fear_greed_index ORDER BY date ASC")
        fear_data = cursor.fetchall()

        # Busca os preços das moedas
        data = []
        for fear_id, fear_date, fear_value, fear_class in fear_data:
            crypto_values = {'fear_date': fear_date, 'fear_value': fear_value}
            for coin in coin_names:
                crypto_values[f"{coin}_max_price"] = 0
                crypto_values[f"{coin}_min_price"] = 0

            cursor.execute("SELECT * FROM model_params WHERE fear_date = %s", (fear_date,))
            for _id, _fear_date, _fear_value, symbol, max_price, min_price in cursor.fetchall():
                crypto_values[f"{symbol}_max_price"] = max_price
                crypto_values[f"{symbol}_min_price"] = min_price

            if len(crypto_values.keys()) > 2:  # Garante que há dados suficientes
                data.append(crypto_values)

        # Cria o DataFrame
        df = pd.DataFrame(data)

        # Converte a coluna de data para datetime
        df["fear_date"] = pd.to_datetime(df["fear_date"])

        # Extrai features de data
        df["year"] = df["fear_date"].dt.year
        df["month"] = df["fear_date"].dt.month
        df["day"] = df["fear_date"].dt.day
        df["day_of_week"] = df["fear_date"].dt.weekday
        df["timestamp"] = df["fear_date"].astype('int64') // 10**9  # Unix timestamp

        # Remove a coluna de data original
        df.drop(columns=["fear_date"], inplace=True)

        logging.info("Dados carregados com sucesso.")
        return df, coin_names

    except Error as e:
        logging.error(f"Erro ao buscar dados: {e}")
        return None, None
