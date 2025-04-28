const mysql = require('mysql2/promise');
const axios = require('axios');
const moment = require('moment');
const fs = require('fs');
const dotenv = require('dotenv');
dotenv.config();

// Criar um stream de escrita para logs
const logStream = fs.createWriteStream('out.log', { flags: 'a' });

function logError(message, error = {}) {
  const errorMessage = `[${new Date().toISOString()}] ${message}: ${error.stack || error.message || error}`;
  console.error(errorMessage);
  logStream.write(errorMessage + '\n');
}

function logInfo(message) {
  const infoMessage = `[${new Date().toISOString()}] ${message}`;
  console.log(infoMessage);
  logStream.write(infoMessage + '\n');
}

// Configuração do Banco de Dados
const DB_CONFIG = {
  host: process.env.DATABASE_HOST,
  port: process.env.DATABASE_PORT,
  user: process.env.DATABASE_USER,
  password: process.env.DATABASE_PASSWORD,
  database: process.env.DATABASE_DBNAME,
};

// Conectar ao banco de dados
async function connectDb() {
  try {
    return await mysql.createConnection(DB_CONFIG);
  } catch (error) {
    logError('Falha na conexão com o banco', error);
    return null;
  }
}

async function disableCrypto(connection, symbol) {
  try {
    await connection.execute(`
      UPDATE cryptos
      SET is_enabled = 0
      WHERE symbol = '${symbol}';
    `);
    await logInfo(`Crypto ${symbol} desativada`)
  } catch (error) {
    logError(`Falha ao desativar crypto ${symbol}`, error);
  }
}

// Buscar símbolos das criptomoedas
async function fetchCryptos(connection) {
  try {
    const [rows] = await connection.execute(`
      SELECT c.id, c.symbol, e.id AS exchange_id
      FROM cryptos c
      JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
      JOIN exchanges e ON ec.exchange_id = e.id
      WHERE LOWER(e.name) LIKE '%binance%'
      AND c.is_enabled = 1;
    `);
    return rows;
  } catch (error) {
    logError('Falha ao buscar criptomoedas da Binance', error);
    return [];
  }
}

// Buscar histórico de preços da Binance
async function fetchCryptoHistory(connection, symbol, START_TIME, END_TIME) {
  const BINANCE_API_URL = 'https://api.binance.com/api/v3/klines';
  const symbolParam = `${symbol}USDT`
  try {
    let pricesHistory = []
    let endDate = END_TIME.clone()
    while(endDate.isAfter(START_TIME)) {
      try {
        let startDate = endDate.clone().subtract(6, 'hours')
        const limit = 10000
        const params = {
          symbol: symbolParam,
          interval: '1m',
          limit,
          startTime: startDate.valueOf(),
          endTime: endDate.valueOf()
        };
        const response = await axios.get(BINANCE_API_URL, { params });

        startTimeStr = startDate.format('YYYY-MM-DD')
        endTimeStr = endDate.format('YYYY-MM-DD')
        logInfo(`Collected: ${startTimeStr} > ${endTimeStr} | ${response.data?.length} of ${symbol}.`);

        pricesHistory = [
          ...pricesHistory,
          ...response.data.map(entry => ({
            OpenTime: entry[0], Open: entry[1], High: entry[2], Low: entry[3], Close: entry[4],
            Volume: entry[5], CloseTime: entry[6], BaseAssetVolume: entry[7], NumberOfTrades: entry[8],
            TakerBuyVolume: entry[9], TakerBuyBaseAssetVolume: entry[10]
          }))
        ]
      } finally { }
      endDate.subtract(6, 'hours')
    }
    return pricesHistory;
  } catch (error) {
    logError(`Falha ao obter dados da Binance para ${symbol}`, error);
    if (error.response?.status === 400) {
      await disableCrypto(connection, symbol);
      return null;
    }

    logError(`Limite de requisições atingido para ${symbol}, tentando novamente em 15 minutos...`);
    await new Promise(resolve => setTimeout(resolve, 15 * 60 * 1000));
    return await fetchCryptoHistory(connection, symbol, DAYS_OFFSET);
  }
}

// Inserir preços no banco de dados
async function insertPriceHistory(connection, priceHistory, crypto) {
  if (!priceHistory || priceHistory.length === 0) {
    return;
  }

  const insertQuery = `
    INSERT INTO cryptos_price_history (
      date, price, crypto_id, exchange_id,
      open_time, open_price, high_price, low_price, close_price, volume,
      close_time, base_asset_volume, number_of_trades, taker_buy_volume, taker_buy_base_asset_volume
    ) VALUES ?
    ON DUPLICATE KEY UPDATE
      price = VALUES(price),
      open_time = VALUES(open_time),
      open_price = VALUES(open_price),
      high_price = VALUES(high_price),
      low_price = VALUES(low_price),
      close_price = VALUES(close_price),
      volume = VALUES(volume),
      close_time = VALUES(close_time),
      base_asset_volume = VALUES(base_asset_volume),
      number_of_trades = VALUES(number_of_trades),
      taker_buy_volume = VALUES(taker_buy_volume),
      taker_buy_base_asset_volume = VALUES(taker_buy_base_asset_volume);
  `;

  const values = priceHistory.map(entry => [
    moment(entry.OpenTime).format('YYYY-MM-DD HH:mm:ss'), entry.Close, crypto.id, crypto.exchange_id,
    entry.OpenTime, entry.Open, entry.High, entry.Low, entry.Close, entry.Volume,
    entry.CloseTime, entry.BaseAssetVolume, entry.NumberOfTrades,
    entry.TakerBuyVolume, entry.TakerBuyBaseAssetVolume
  ]);

  try {
    await connection.query(insertQuery, [values]);
  } catch (error) {
    logError(`Erro ao inserir histórico de ${crypto.symbol}`, error);
  }
}

// Executar fluxo principal
(async () => {
  try {
    const connection = await connectDb();
    if (!connection) return;

    const cryptos = await fetchCryptos(connection);
    const daysOffset = 0; // ex: batchSize offset
    const batchSize = 90; // Dias de dados buscados

    for (let i = 0; i < batchSize; i++) {
      const END_TIME = moment().utc().startOf('day').subtract(daysOffset, 'days');
      const START_TIME = END_TIME.clone().subtract(batchSize, 'days');

      startTimeStr = START_TIME.format('YYYY-MM-DD')
      endTimeStr = END_TIME.format('YYYY-MM-DD')

      logInfo(`Interval: ${startTimeStr} > ${endTimeStr} | ${cryptos.length} Cryptos.`);

      for (const crypto of cryptos) {
        const history = await fetchCryptoHistory(connection, crypto.symbol, START_TIME, END_TIME);
        logInfo(`${startTimeStr} > ${endTimeStr} | ${Number(history?.length)} history for ${crypto.symbol}.`);
        await insertPriceHistory(connection, history, crypto);
      }
    }

    await connection.end();
  } catch (error) {
    logError('Falha geral', error);
  }
})();
