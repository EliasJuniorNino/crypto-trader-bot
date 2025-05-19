import os
import mysql.connector
import sqlite3
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carrega variáveis do .env (se aplicável)
load_dotenv()

# Configurações do MySQL
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST"),
    "port": int(os.getenv("DATABASE_PORT", 3306)),
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "database": os.getenv("DATABASE_DBNAME")
}

# Caminho do banco SQLite
SQLITE_DB_PATH = "database.db"  # Certifique-se de que este arquivo já existe com a tabela 'cryptos'

if __name__ == "__main__":
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        with open("create_database.sql", "r") as f:
            cursor.executescript(f.read())
            
    mysql_conn = mysql.connector.connect(**DB_CONFIG)
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)  
    
    mysql_cursor = mysql_conn.cursor()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_cursor.execute("SELECT symbol, name, is_enabled FROM cryptos;")
    for row in mysql_cursor.fetchall():
        query = "INSERT OR IGNORE INTO cryptos (symbol, name, is_enabled) VALUES (?, ?, ?);"
        sqlite_cursor.execute(query,  row)
        
    mysql_cursor.execute("SELECT name FROM exchanges;")
    for row in mysql_cursor.fetchall():
        query = "INSERT OR IGNORE INTO exchanges (name) VALUES (?);"
        sqlite_cursor.execute(query,  row)
        
    mysql_cursor.execute("SELECT crypto_id, exchange_id FROM exchanges_cryptos;")
    for (mysql_crypto_id, mysql_exchange_id) in mysql_cursor.fetchall():
        mysql_cursor.execute("SELECT symbol FROM cryptos WHERE id = %s;", (mysql_crypto_id,))
        crypto_symbol, = mysql_cursor.fetchone()
        
        mysql_cursor.execute("SELECT name FROM exchanges WHERE id = %s;", (mysql_exchange_id,))
        exchange_name, = mysql_cursor.fetchone()
        
        # buscar id da exchange no sqlite
        sqlite_cursor.execute("SELECT id FROM exchanges WHERE LOWER(name) = LOWER(?);", (exchange_name,))
        exchange_id, = sqlite_cursor.fetchone()
        
        # Busca id da crypto no sqlite
        sqlite_cursor.execute("SELECT id FROM cryptos WHERE LOWER(symbol) = LOWER(?);", (crypto_symbol,))
        crypto_id, = sqlite_cursor.fetchone()
        
        query = "INSERT OR IGNORE INTO exchanges_cryptos (exchange_id, crypto_id) VALUES (?, ?);"
        sqlite_cursor.execute(query, (exchange_id, crypto_id))
        
    if mysql_conn.is_connected():
        mysql_conn.close()
        
    sqlite_conn.commit()
    sqlite_conn.close()
        
    
