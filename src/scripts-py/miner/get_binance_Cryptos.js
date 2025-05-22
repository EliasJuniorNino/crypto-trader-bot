const mysql = require('mysql2/promise');
const axios = require('axios');
const dotenv = require('dotenv');
dotenv.config();

// Configurações da API Binance
const API_URL_BINANCE = "https://api.binance.com/api/v1/exchangeInfo";

// Configurações do Banco de Dados
const DB_CONFIG = {
  host: process.env.DATABASE_HOST,
  port: process.env.DATABASE_PORT,
  user: process.env.DATABASE_USER,
  password: process.env.DATABASE_PASSWORD,
  database: process.env.DATABASE_DBNAME,
};

// Função para conectar ao banco de dados
async function connectDb() {
  try {
    const connection = await mysql.createConnection(DB_CONFIG);
    console.log("[Sucesso] Conexão com o banco de dados estabelecida.");
    return connection;
  } catch (error) {
    console.error("[Erro] Falha na conexão com o banco: ", error);
    return null;
  }
}

// Função para buscar a lista de criptomoedas da Binance
async function fetchBinanceCryptos() {
  try {
    const response = await axios.get(API_URL_BINANCE, { timeout: 10000 });
    if (response.data && response.data.symbols) {
      return response.data.symbols.map(symbol => [symbol.baseAsset]);
    } else {
      console.error("[Erro] Resposta inesperada da API:", response.data);
      return null;
    }
  } catch (error) {
    console.error("[Erro] Falha ao obter dados da API:", error);
    return null;
  }
}

async function getBinanceExchangeID(connection) {
  const sqlQuery = `SELECT * FROM exchanges WHERE name = 'binance';`;

  try {
    const [result] = await connection.query(sqlQuery);
    return result[0].id
  } catch (error) {
    console.error("[Erro] Falha ao buscar exchange:", error);
  }
}

// Função para inserir os símbolos no banco de dados
async function insertBinanceCryptos(connection, binanceCryptosNames) {
  if (!binanceCryptosNames || binanceCryptosNames.length === 0) {
    console.warn("[Aviso] Nenhum dado para inserir.");
    return;
  }

  try {
    const [result] = await connection.query(
      `INSERT INTO cryptos (symbol) VALUES ? ON DUPLICATE KEY UPDATE symbol = symbol;`,
      [binanceCryptosNames.map(symbol => [symbol])]
    );

    console.log(`[Sucesso] ${result.affectedRows} criptomoedas inseridas/atualizadas com sucesso!`);
  } catch (error) {
    console.error("[Erro] Falha ao inserir criptomoedas:", error);
  }
}

async function linkBinanceCryptosWithExchange(connection, binanceCryptosNames, binanceExchangeId) {
  if (!binanceCryptosNames || binanceCryptosNames.length === 0) {
    console.warn("[Aviso] Nenhum dado para inserir.");
    return;
  }

  try {
    const [binancCryptosResult] = await connection.query(
      `
      SELECT *
      FROM cryptos
      WHERE symbol IN (?)
      `,
      [binanceCryptosNames]
    );

    await connection.query(
      `
      INSERT INTO exchanges_cryptos (crypto_id, exchange_id) VALUES ?
      ON DUPLICATE KEY UPDATE crypto_id = crypto_id, exchange_id = exchange_id;`,
      [binancCryptosResult.map((result) => [result.id, binanceExchangeId])]
    );

    console.log(`[Sucesso] linkBinanceCryptosWithExchange!`);
  } catch (error) {
    console.error("[Erro] linkBinanceCryptosWithExchange:", error);
  }

}

// Executar o fluxo principal
async function main() {
  const dbConn = await connectDb();
  if (dbConn) {
    const binanceExchangeId = await getBinanceExchangeID(dbConn);
    const cryptos = await fetchBinanceCryptos();
    if (cryptos) {
      await insertBinanceCryptos(dbConn, cryptos);
      await linkBinanceCryptosWithExchange(dbConn, cryptos, binanceExchangeId)
    }
    await dbConn.end();
    console.log("[Sucesso] Conexão com o banco de dados fechada.");
  }
}

main();
