import os
import requests
import zipfile
from time import sleep
import logging
from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Caminho para o banco SQLite - altere para o seu caminho
SQLITE_DB_PATH = "database.db"

# Arquivo para armazenar o progresso
PROGRESS_FILE = "data/progress.json"

def connect_db():
    try:
        connection = sqlite3.connect(SQLITE_DB_PATH)
        logging.info("Conexão com o banco SQLite estabelecida.")
        return connection
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco SQLite: {e}")
        return None

def get_enabled_cryptos():
    db_connection = connect_db()
    if not db_connection:
        return []

    try:
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT c.id, c.symbol, e.id AS exchange_id, c.is_enabled
            FROM cryptos c
            JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
            JOIN exchanges e ON ec.exchange_id = e.id
            WHERE LOWER(e.name) LIKE '%binance%'
            AND c.is_enabled = 1;
        """)
        result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        logging.error(f"Erro ao buscar criptos: {e}")
        return []
    finally:
        db_connection.close()

def save_progress_data(last_processed_date=None, started_date=None):
    """Salva datas no arquivo de progresso."""
    try:
        data = {}
        # Carrega dados antigos, se existirem
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
        
        if last_processed_date:
            data['last_processed_date'] = last_processed_date.strftime("%Y-%m-%d")
        if started_date:
            data['started_date'] = started_date.strftime("%Y-%m-%d")

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        logging.info(f"📌 Progresso salvo: {data}")
    except Exception as e:
        logging.error(f"Erro ao salvar progresso: {e}")

def load_last_processed_date():
    """Carrega a última data processada do arquivo de progresso."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                last_date = data.get('last_processed_date')
                if last_date:
                    return datetime.strptime(last_date, "%Y-%m-%d")
        except Exception as e:
            logging.error(f"Erro ao carregar progresso: {e}")
    
    # Se não houver arquivo de progresso ou ocorrer erro, retorne a data atual
    return datetime.now() - timedelta(days=1)

def load_started_date():
    """Carrega a data de início do download do arquivo de progresso."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                started_date = data.get('started_date')
                if started_date:
                    return datetime.strptime(started_date, "%Y-%m-%d")
        except Exception as e:
            logging.error(f"Erro ao carregar data de início: {e}")
    
    # Se não houver arquivo de progresso ou ocorrer erro, retorne a data atual
    return datetime.now()

def download_and_extract_klines(pairs=["BTCUSDT"], interval="1m", days_to_process=30, min_date="2017-01-01", max_date=None, save_dir="binance_data"):
    """
    Baixa e extrai arquivos de Klines da Binance, indo da data atual para o passado.
    
    Args:
        pairs: Lista de pares de trading (ex: ["BTCUSDT", "ETHUSDT"])
        interval: Intervalo de tempo (ex: "1m", "1h", "1d")
        days_to_process: Número de dias a processar antes de parar 
                        (0 para processar até min_date)
        min_date: Data mínima no formato "YYYY-MM-DD" para parar o processamento
        save_dir: Diretório para salvar os dados
    """
    # Definir max_date se não fornecido
    if max_date is None:
        max_date = datetime.now().strftime("%Y-%m-%d")
        
    # Carregar a última data processada ou usar a data atual
    current_date = datetime.strptime(max_date, "%Y-%m-%d")
    min_datetime = datetime.strptime(min_date, "%Y-%m-%d")
    
    # Salva a data de início do download
    save_progress_data(started_date=current_date)
    
    # Contador de dias processados
    days_processed = 0
    
    # Processar enquanto não atingir o limite de dias ou a data mínima
    while (days_to_process == 0 or days_processed < days_to_process) and current_date >= min_datetime:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        
        for index, symbol in enumerate(pairs):
            print('')
            logging.info(f"👉  {symbol}({index + 1}/{len(pairs)})")
            base_url = "https://data.binance.vision/data/spot/daily/klines"
            zip_dir = os.path.join(save_dir, symbol, interval, "zip")
            csv_dir = os.path.join(save_dir, symbol, interval, "csv")

            os.makedirs(zip_dir, exist_ok=True)
            os.makedirs(csv_dir, exist_ok=True)

            month_str = f"{month:02d}"
            day_str = f"{day:02d}"
            file_name = f"{symbol}-{interval}-{year}-{month_str}-{day_str}.zip"
            url = f"{base_url}/{symbol}/{interval}/{file_name}"
            zip_path = os.path.join(zip_dir, file_name)

            if os.path.exists(os.path.join(csv_dir, file_name.replace(".zip", ".csv"))):
                logging.info(f"✅ Já extraído: {file_name}")
                continue

            logging.info(f"⬇️  Baixando: {url}")
            try:
                response = requests.get(url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(zip_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logging.info(f"✔️  Salvo: {zip_path}")
                else:
                    logging.warning(f"❌ Arquivo não encontrado: {file_name} (status {response.status_code})")
                    continue
            except Exception as e:
                logging.error(f"⚠️ Erro ao baixar {file_name}: {e}")
                continue

            # Extrair o ZIP
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(csv_dir)
                    logging.info(f"📦 Extraído para: {csv_dir}")
            except Exception as e:
                logging.error(f"❌ Erro ao extrair {zip_path}: {e}")

            sleep(1)
        
        # Salvar o progresso atual antes de ir para o próximo dia
        save_progress_data(last_processed_date=current_date)
        
        # Ir para o dia anterior
        current_date -= timedelta(days=1)
        days_processed += 1
        
        # Log de progresso
        logging.info(f"📅 Processado dia: {current_date.strftime('%Y-%m-%d')} ({days_processed} dias)")

# Main function
if __name__ == "__main__":
    cryptos = get_enabled_cryptos()
    if len(cryptos) > 0:
        # Pega data inicial da ultima vez
        started_date = load_started_date()
        today = datetime.now()
        one_day_ago = today - timedelta(days=1)

        # Verifica se a data de início é menor que ontem
        if started_date.date() < one_day_ago.date():
            logging.info(f"📅 Recuperando dados recentes até: {started_date.strftime('%Y-%m-%d')}")
            download_and_extract_klines(
                pairs=[f"{crypto[1]}USDT" for crypto in cryptos],
                interval="1m",  # Corrigido de 1s para 1m
                days_to_process=0,
                min_date=started_date.strftime('%Y-%m-%d'),
                max_date=one_day_ago.strftime('%Y-%m-%d'),
                save_dir="data/binance_data"
            )

        # Segunda parte: histórico completo até 2017
        last_processed = load_last_processed_date()
        download_and_extract_klines(
            pairs=[f"{crypto[1]}USDT" for crypto in cryptos],
            interval="1m",  # Corrigido de 1s para 1m
            days_to_process=0,
            min_date="2017-01-01",
            max_date=last_processed.strftime('%Y-%m-%d'),
            save_dir="data/binance_data"
        )

        