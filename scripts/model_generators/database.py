import mysql.connector
from mysql.connector import Error
import logging
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST"),
    "port": int(os.getenv("DATABASE_PORT", 3306)),  # Valor padrão 3306 se não definido
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_DBNAME")
}

def connect_db():
    """Conecta ao banco de dados e retorna a conexão."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logging.info("Conexão com o banco de dados estabelecida.")
            return connection
    except Error as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        return None
