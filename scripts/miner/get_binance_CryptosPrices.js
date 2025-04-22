const mysql = require('mysql2/promise');
const axios = require('axios');
const moment = require('moment');
const dotenv = require('dotenv');
dotenv.config();

// Configurações do Banco de Dados
const DB_CONFIG = {
  host: process.env.DATABASE_HOST,
  port: process.env.DATABASE_PORT,
  user: process.env.DATABASE_USER,
  password: process.env.DATABASE_PASSWORD,
  database: process.env.DATABASE_DBNAME,
};

// Configuração da API Binance
const BINANCE_API_URL = 'https://api.binance.com/api/v3/klines';
const INTERVAL = '1m';
const LIMIT = 60 * 24;

const DATE_OFFSET = moment().subtract(2, 'days').startOf('day');
const START_TIME = DATE_OFFSET.unix() * 1000;
const END_TIME = moment().subtract(1, 'days').startOf('day').unix() * 1000;

console.log(`Collecting from ${moment(START_TIME).format()} to ${moment(END_TIME).format()}`);

async function connectDb() {
  try {
    const connection = await mysql.createConnection(DB_CONFIG);
    return connection;
  } catch (error) {
    console.error('[Erro] Falha na conexão com o banco:', error);
    return null;
  }
}

async function fetchCryptoSymbols(connection) {
  const [rows] = await connection.execute('SELECT symbol FROM cryptos ');
  return rows.map(row => row.symbol);
}

async function fetchCryptoHistory(symbol) {
  const symbolPair = `${symbol}USDT`;
  const params = {
    symbol: symbolPair,
    interval: INTERVAL,
    limit: LIMIT,
    startTime: START_TIME,
    endTime: END_TIME
  };

  try {
    const response = await axios.get(BINANCE_API_URL, { params, timeout: 10000 });
    const priceHistory = response.data.map(entry => ({
      timestamp: entry[0] / 1000,
      price: parseFloat(entry[4])
    }));
    return { status: 200, priceHistory };
  } catch (error) {
    console.error(`[Erro] Falha ao obter dados da Binance para ${symbol}:`, error.message);
    return { status: error.response?.status || 429, priceHistory: null };
  }
}

async function insertPriceHistory(connection, symbol, priceHistory) {
  if (!priceHistory.length) {
    console.log(`[Aviso] Nenhum histórico de preços disponível para ${symbol}.`);
    return;
  }

  const insertQuery = `
    INSERT INTO coin_price_history (exchange, coin, timestamp, date, price)
    VALUES ('binance', ?, ?, ?, ?)
    ON DUPLICATE KEY UPDATE price = VALUES(price);
    `;

  try {
    const promises = priceHistory.map(entry => {
      const date = moment.unix(entry.timestamp).format('YYYY-MM-DD HH:mm:ss');
      return connection.execute(insertQuery, [symbol, entry.timestamp, date, entry.price]);
    });
    await Promise.all(promises);
    console.log(`[Sucesso] Histórico de ${symbol} armazenado com sucesso.`);
  } catch (error) {
    console.error(`[Erro] Falha ao inserir histórico de ${symbol}:`, error.message);
  }
}

(async () => {
  const connection = await connectDb();
  if (connection) {
    const symbols = await fetchCryptoSymbols(connection);
    for (const symbol of symbols) {
      let { status, priceHistory } = await fetchCryptoHistory(symbol);
      while (!priceHistory && status === 429) {
        console.log(`[Aviso] Limite de requisições atingido para ${symbol}. Tentando novamente em 1 minuto...`);
        await new Promise(resolve => setTimeout(resolve, 60000));
        ({ status, priceHistory } = await fetchCryptoHistory(symbol));
      }
      if (priceHistory) {
        await insertPriceHistory(connection, symbol, priceHistory);
      }
    }
    await connection.end();
  }
})();
