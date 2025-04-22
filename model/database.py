import mysql.connector
from mysql.connector import Error
import logging


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "admin",
    "password": "admin",
    "database": "database"
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
