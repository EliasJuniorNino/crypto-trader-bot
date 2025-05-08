require('dotenv').config();
const axios = require('axios');
const mysql = require('mysql2/promise');
const dotenv = require('dotenv');
dotenv.config();

// Configurações da API
const API_KEY = process.env.COINMARKETCAP_API_KEY;
const API_URL = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical";
const HEADERS = { "X-CMC_PRO_API_KEY": API_KEY };

// Configurações do Banco de Dados
const DB_CONFIG = {
  host: process.env.DATABASE_HOST,
  port: process.env.DATABASE_PORT,
  user: process.env.DATABASE_USER,
  password: process.env.DATABASE_PASSWORD,
  database: process.env.DATABASE_DBNAME,
};

// Função para converter timestamp Unix para DATETIME do MySQL
function convertToMySQLDatetime(epochTimestamp) {
  try {
    return new Date(epochTimestamp * 1000).toISOString().slice(0, 19).replace('T', ' ');
  } catch (error) {
    console.error(`Erro ao converter timestamp: ${error}`);
    return null;
  }
}

// Função para obter dados da API
async function fetchData(limit, start = null) {
  try {
    const params = { limit };
    if (start) params.start = start;

    const response = await axios.get(API_URL, { headers: HEADERS, params, timeout: 10000 });
    return response.data.data || null;
  } catch (error) {
    console.error(`Erro na requisição da API: ${error.message}`);
    console.error(error)
    return null;
  }
}

// Função para conectar ao banco de dados
async function connectDB() {
  try {
    return await mysql.createConnection(DB_CONFIG);
  } catch (error) {
    console.error(`Erro ao conectar ao banco: ${error.message}`);
    return null;
  }
}

// Função para verificar se o registro já existe no banco
async function recordExists(connection, timestamp) {
  const [rows] = await connection.execute(`
    SELECT 1
    FROM fear_index
    WHERE date = ? AND source = 'CoinMarketCap'
    LIMIT 1
  `, [timestamp]);
  return rows.length > 0;
}

// Função para inserir dados no banco
async function insertData(connection, data) {
  if (!data || data.length === 0) {
    console.log("Nenhum dado disponível para inserção.");
    return;
  }

  const insertQuery = "INSERT INTO fear_index (source, target, date, value) VALUES (?, ?, ?, ?)";
  let insertedCount = 0;

  for (const item of data) {
    const convertedTimestamp = convertToMySQLDatetime(item.timestamp);
    if (convertedTimestamp && !(await recordExists(connection, convertedTimestamp))) {
      try {
        await connection.execute(insertQuery, ["CoinMarketCap", null, convertedTimestamp, item.value]);
        insertedCount++;
      } catch (error) {
        console.error(`Erro ao inserir dados: ${error.message}`);
      }
    } else {
      console.log(`Registro com timestamp ${convertedTimestamp} já existe, ignorando.`);
    }
  }

  console.log(`${insertedCount} registros inseridos com sucesso!`);
}

// Executar o fluxo
(async () => {
  const dbConn = await connectDB();
  if (dbConn) {
    const data = await fetchData(30);
    if (data) {
      await insertData(dbConn, data);
    }
    await dbConn.end();
  }
})();
