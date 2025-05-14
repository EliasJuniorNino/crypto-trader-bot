const mysql = require('mysql2/promise');
const axios = require('axios');
const moment = require('moment');
const fs = require('fs');
const dotenv = require('dotenv');
dotenv.config();

// Criar um stream de escrita para logs
const logStream = fs.createWriteStream('out.log', { flags: 'a' });

function logError(message, error = {}) {
  const currentTimeStr = moment().format("YYYY-MM-DD HH:mm:ss");
  const errorMessage = `[${currentTimeStr}] ${message}: ${error.stack || error.message || error}`;
  console.error(errorMessage);
  logStream.write(errorMessage + '\n');
}

function logInfo(message) {
  const currentTimeStr = moment().format("YYYY-MM-DD HH:mm:ss");
  const infoMessage = `[${currentTimeStr}] ${message}`;
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

async function disableNotCollectableCryptos(connection) {
  const cryptosToDisable = []
  try {
    const [cryptos] = await connection.execute(`
      SELECT c.id, c.symbol, e.id AS exchange_id
      FROM cryptos c
      JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
      JOIN exchanges e ON ec.exchange_id = e.id
      WHERE LOWER(e.name) LIKE '%binance%'
      AND c.is_enabled = 1;
    `);

    const BINANCE_API_URL = 'https://api.binance.com/api/v3/klines';
    for (let i = 0; i < cryptos.length; i++) {
      const symbol = cryptos[i].symbol
      const symbolParam = `${symbol}USDT`
      const limit = 1
      const params = {
        symbol: symbolParam,
        interval: '1m',
        limit,
        startTime: moment().startOf('day').subtract(1, 'days').valueOf(),
        endTime: moment().startOf('day').valueOf()
      };
      const response = await axios.get(BINANCE_API_URL, { params });
      if (!response.data?.length) {
        cryptosToDisable.push(symbol)
      }
    }

  } finally { }

  logInfo(`Cryptos do disable: ${JSON.stringify(cryptosToDisable)}`);
  try {
    if (cryptosToDisable.length) {
      const placeholders = cryptosToDisable.map(() => '?').join(', ');
      await connection.execute(`
        UPDATE cryptos
        SET is_enabled = 0
        WHERE symbol IN (${placeholders})
      `, cryptosToDisable);
    }
  } catch (error) {
    logError(`Falha ao desativar cryptos`, error);
  }
}

// Buscar símbolos das criptomoedas
async function fetchCryptos(connection) {
  logInfo(`Searching for cryptos to collect...`);

  try {
    const [cryptos] = await connection.execute(`
      SELECT c.id, c.symbol, e.id AS exchange_id
      FROM cryptos c
      JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
      JOIN exchanges e ON ec.exchange_id = e.id
      WHERE LOWER(e.name) LIKE '%binance%'
      AND c.is_enabled = 1;
    `);
    return cryptos;
  } catch (error) {
    logError('Falha ao buscar criptomoedas da Binance', error);
    return [];
  }
}

// Buscar histórico de preços da Binance
async function fetchCryptoHistory(connection, symbol, currentDay) {
  const BINANCE_API_URL = 'https://api.binance.com/api/v3/klines';
  const symbolParam = `${symbol}USDT`
  try {
    let pricesHistory = []
    let endDate = currentDay.utc().startOf('day').clone().add(1, 'day')
    let startDate = endDate.clone().subtract(6, 'hours')
    while (startDate.isSameOrAfter(currentDay.utc().startOf('day'))) {
      try {
        const limit = 10000
        const params = {
          symbol: symbolParam,
          interval: '1m',
          limit,
          startTime: startDate.valueOf(),
          endTime: endDate.valueOf()
        };
        const response = await axios.get(BINANCE_API_URL, { params });

        pricesHistory = [
          ...pricesHistory,
          ...response.data.map(entry => ({
            OpenTime: entry[0], Open: entry[1], High: entry[2], Low: entry[3], Close: entry[4],
            Volume: entry[5], CloseTime: entry[6], BaseAssetVolume: entry[7], NumberOfTrades: entry[8],
            TakerBuyVolume: entry[9], TakerBuyBaseAssetVolume: entry[10]
          }))
        ]
      } catch {
        startTimeStr = startDate.format('YYYY-MM-DD HH:mm')
        endTimeStr = endDate.format('YYYY-MM-DD HH:mm')
        logError(`Falha ao colletar ${symbol} no intervalo ${startTimeStr} -> ${endTimeStr}`)
      } finally {
        startDate.subtract(6, 'hours')
        endDate.subtract(6, 'hours')
      }
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

function calcularTempoRestante(percentual, tempoGastoSegundos) {
  // Converte percentual para decimal
  const porcentagem = parseFloat(percentual) / 100;

  if (porcentagem <= 0 || porcentagem >= 1) {
    return "...";
  }

  // Calcula tempo total estimado
  const tempoTotalEstimado = tempoGastoSegundos / porcentagem;

  // Calcula o tempo restante
  const tempoRestanteSegundos = tempoTotalEstimado - tempoGastoSegundos;

  // Converte tempo restante de segundos para "HH:MM:SS"
  const horas = Math.floor(tempoRestanteSegundos / 3600);
  const minutos = Math.floor((tempoRestanteSegundos % 3600) / 60);
  const segundos = Math.floor(tempoRestanteSegundos % 60);

  const pad = (n) => n.toString().padStart(2, '0');
  return `${pad(horas)}:${pad(minutos)}:${pad(segundos)}`;
}


// Executar fluxo principal
(async () => {
  try {
    const connection = await connectDb();
    if (!connection) return;

    //await disableNotCollectableCryptos();
    const cryptos = await fetchCryptos(connection);
    const cryptosCount = cryptos.length;
    const startDayInterval = moment('2024-12-07', 'YYYY-MM-DD').utc().startOf('day');
    const endDayInterval = moment('2025-12-07', 'YYYY-MM-DD').utc().startOf('day');

    logInfo(`From ${startDayInterval.format('YYYY-MM-DD')} to ${endDayInterval.format('YYYY-MM-DD')} | ${cryptos.length} Cryptos.`);
    
    const scriptStartedTime = moment();
    let currentDay = endDayInterval.clone();
    while (currentDay.isSameOrAfter(startDayInterval)) {
      try {
        for (let cryptoIndex = 0; cryptoIndex < cryptosCount; cryptoIndex++) {
          const crypto = cryptos[cryptoIndex];
          const history = await fetchCryptoHistory(connection, crypto.symbol, currentDay);
          const historiesCount = Number(history?.length);

          const now = moment();
          const elapsedSeconds = now.diff(scriptStartedTime, 'seconds');
          const elapsedDuration = moment.duration(elapsedSeconds, 'seconds');
          const elapsedHours = String(elapsedDuration.hours()).padStart(2, '0');
          const elapsedMinutes = String(elapsedDuration.minutes()).padStart(2, '0');
          const elapsedSecounds = String(elapsedDuration.seconds()).padStart(2, '0');
          const elapsedTime = `${elapsedHours}:${elapsedMinutes}:${elapsedSecounds}`;

          logInfo(`${elapsedTime} | ${currentDay.format('YYYY-MM-DD')} | ${historiesCount} histories - ${crypto.symbol}`);
          await insertPriceHistory(connection, history, crypto);
        }
      }
      finally {
        currentDay = currentDay.subtract(1, 'days')
      }
    }

    await connection.end();
  } catch (error) {
    logError('Falha geral', error);
  }
})();
