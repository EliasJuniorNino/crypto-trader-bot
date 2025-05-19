const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const { Decimal } = require('decimal.js');
require('dotenv').config();

async function fetchCryptosAndPrices(connection) {
    const [cryptos] = await connection.execute(`
        SELECT c.id, c.symbol, e.id AS exchange_id, c.is_enabled
        FROM cryptos c
        JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
        JOIN exchanges e ON ec.exchange_id = e.id
        WHERE LOWER(e.name) LIKE '%binance%'
        AND c.is_enabled = 1;
    `);
    console.log(`${cryptos.length} Cryptos found.`);

    const [fearTicks] = await connection.execute(`
        SELECT * FROM (
            SELECT
                DATE(date) AS datetime,
                YEAR(date) AS year,
                MONTH(date) AS month,
                DAY(date) AS day,
                MAX(CASE WHEN source = 'api.alternative.me' THEN value END) AS fear_api_alternative_me,
                MAX(CASE WHEN source = 'CoinMarketCap' THEN value END) AS fear_coinmarketcap
            FROM fear_index
            WHERE value IS NOT NULL
            GROUP BY date
            ORDER BY date ASC
        ) f
        WHERE fear_api_alternative_me IS NOT NULL AND fear_coinmarketcap IS NOT NULL;
    `);
    console.log(`${fearTicks.length} FearTicks found.`);

    const [prices] = await connection.execute(`
        SELECT
            YEAR(cph.date) AS year,
            MONTH(cph.date) AS month,
            DAY(cph.date) AS day,
            HOUR(cph.date) AS hour,
            c.symbol,
            MIN(cph.price) AS min_value, 
            MAX(cph.price) AS max_value,
            c.is_enabled AS is_enabled
        FROM cryptos_price_history cph
        JOIN cryptos c ON c.id = cph.crypto_id
        WHERE c.is_enabled = 1
        GROUP BY year, month, day, hour, c.symbol
        ORDER BY year ASC, month ASC, day ASC, hour ASC;
    `);
    console.log(`${prices.length} Prices found.`);

    const priceMap = {};
    for (const row of prices) {
        const key = `${row.year}-${String(row.month).padStart(2, '0')}-${String(row.day).padStart(2, '0')} ${String(row.hour).padStart(2, '0')}:00:00`;
        if (!priceMap[key]) priceMap[key] = [];

        try {
            priceMap[key].push({
                symbol: row.symbol,
                min_value: new Decimal(row.min_value || 0),
                max_value: new Decimal(row.max_value || 0)
            });
        } catch (err) {
            console.error(`Error parsing price: ${err}`);
        }
    }

    console.log("PriceHistory map generated.");
    return { cryptos, fearTicks, priceMap };
}

function isRowValid(row) {
    const total = row.length;
    const emptyQtd = row.filter(cell => cell.trim() === '0').length;
    if (total === 0) return false;
    return emptyQtd / total <= 0.6;
}

function generateCSV(fearTicks, cryptos, priceMap) {
    const outputPath = path.join('data', 'dataset2.csv');
    fs.mkdirSync('data', { recursive: true });

    const header = ['year', 'month', 'day', 'hour', 'fear_api_alternative_me', 'fear_coinmarketcap'];
    for (const crypto of cryptos) {
        header.push(`${crypto.symbol}_min_value`, `${crypto.symbol}_max_value`);
    }

    const lines = [header.join(',')];
    let rowsCount = 0;

    for (const tick of fearTicks) {
        for(let h = 0; h < 24; h++) {
            const row = [
                tick.year,
                tick.month,
                tick.day,
                h,
                tick.fear_api_alternative_me,
                tick.fear_coinmarketcap
            ];

            const dateKey = `${tick.year}-${String(tick.month).padStart(2, '0')}-${String(tick.day).padStart(2, '0')} ${String(h).padStart(2, '0')}:00:00`;
            const priceList = priceMap[dateKey] || [];
            const priceDict = Object.fromEntries(
                priceList.map(p => [p.symbol, [p.min_value, p.max_value]])
            );

            for (const crypto of cryptos) {
                const prices = priceDict[crypto.symbol];
                if (prices) {
                    row.push(prices[0].toString(), prices[1].toString());
                } else {
                    row.push('0', '0');
                }
            }

            const dataPart = row.slice(5);
            if (isRowValid(dataPart)) {
                lines.push(row.join(','));
                rowsCount++;
            }
        }
    }

    fs.writeFileSync(outputPath, lines.join('\n'));
    console.log(`CSV rows: ${rowsCount}`);
}

async function main() {
    try {
        const connection = await mysql.createConnection({
            host: process.env.DATABASE_HOST,
            port: process.env.DATABASE_PORT,
            user: process.env.DATABASE_USER,
            password: process.env.DATABASE_PASSWORD,
            database: process.env.DATABASE_DBNAME
        });

        const { cryptos, fearTicks, priceMap } = await fetchCryptosAndPrices(connection);
        generateCSV(fearTicks, cryptos, priceMap);

        await connection.end();
        console.log("CSV file generated successfully!");
    } catch (err) {
        console.error("SQL error:", err);
    }
}

main();
