#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <mysql_driver.h>
#include <mysql_connection.h>
#include <cppconn/prepared_statement.h>
#include <cppconn/resultset.h>
#include <cppconn/statement.h>
#include <ctime>
#include <iomanip>
#include <boost/multiprecision/cpp_dec_float.hpp>

using namespace std;

typedef boost::multiprecision::cpp_dec_float_50 cpp_dec_float;

struct Crypto
{
    int id;
    string symbol;
    int exchange_id;
};

struct FearTick
{
    string datetimeStr;
    time_t datetime;
    int year;
    int month;
    int day;
    double fear_api_alternative_me;
    double fear_coinmarketcap;
};

struct PriceHistory
{
    string symbol;
    string currentDate;
    cpp_dec_float min_value; // Usando cpp_dec_float para alta precisão
    cpp_dec_float max_value; // Usando cpp_dec_float para alta precisão
};

time_t stringToTime(const string &datetimeStr)
{
    std::tm tm = {};
    strptime(datetimeStr.c_str(), "%Y-%m-%d", &tm);
    return mktime(&tm);
}

void fetchCryptosAndPrices(sql::Connection *con, vector<Crypto> &cryptos, vector<FearTick> &fearTicks, map<string, vector<PriceHistory>> &priceMap)
{
    sql::Statement *stmt = con->createStatement();

    // Fetch cryptocurrencies
    sql::ResultSet *res = stmt->executeQuery(R"(
        SELECT c.id, c.symbol, e.id AS exchange_id
        FROM cryptos c
        JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
        JOIN exchanges e ON ec.exchange_id = e.id
        WHERE LOWER(e.name) LIKE '%binance%';
    )");
    while (res->next())
    {
        Crypto crypto;
        crypto.id = res->getInt("id");
        crypto.symbol = res->getString("symbol");
        crypto.exchange_id = res->getInt("exchange_id");
        cryptos.push_back(crypto);
    }
    delete res;
    std::cout << cryptos.size() << " Cryptos found." << std::endl;

    // Fetch fear index ticks
    res = stmt->executeQuery(R"(
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
    )");
    while (res->next())
    {
        FearTick fearTick;
        fearTick.datetimeStr = res->getString("datetime");
        fearTick.datetime = stringToTime(fearTick.datetimeStr);
        fearTick.year = res->getInt("year");
        fearTick.month = res->getInt("month");
        fearTick.day = res->getInt("day");
        fearTick.fear_api_alternative_me = res->getDouble("fear_api_alternative_me");
        fearTick.fear_coinmarketcap = res->getDouble("fear_coinmarketcap");
        fearTicks.push_back(fearTick);
    }
    delete res;
    std::cout << fearTicks.size() << " FearTicks found." << std::endl;

    // Fetch price history and map by date
    res = stmt->executeQuery(R"(
        SELECT
            DATE_FORMAT(cph.date, '%Y-%m-%d') AS currentDate, 
            c.symbol,
            MIN(cph.price) AS min_value, 
            MAX(cph.price) AS max_value
        FROM cryptos_price_history cph
        JOIN cryptos c ON c.id = cph.crypto_id
        GROUP BY currentDate, c.symbol
        ORDER BY STR_TO_DATE(currentDate, '%Y-%m-%d') ASC;
    )");
    while (res->next())
    {
        PriceHistory priceHistory;
        priceHistory.symbol = res->getString("symbol");
        priceHistory.currentDate = res->getString("currentDate");

        // Use cpp_dec_float for higher precision values
        string min_value_str = res->getString("min_value");
        string max_value_str = res->getString("max_value");

        try
        {
            if (!min_value_str.empty())
            {
                priceHistory.min_value = cpp_dec_float(min_value_str);
            }
            else
            {
                priceHistory.min_value = cpp_dec_float(0); // Valor padrão
            }

            if (!max_value_str.empty())
            {
                priceHistory.max_value = cpp_dec_float(max_value_str);
            }
            else
            {
                priceHistory.max_value = cpp_dec_float(0); // Valor padrão
            }
        }
        catch (const std::exception &e)
        {
            std::cerr << "Erro: " << e.what() << std::endl;
        }

        priceMap[priceHistory.currentDate].push_back(priceHistory);
    }
    delete res;
    std::cout << "PriceHistory map generated." << std::endl;

    delete stmt;
}

int isRowValid(const stringstream &rowStream)
{
    string row = rowStream.str();
    int totalFields = 0;
    int emptyFields = 0;

    stringstream ss(row);
    string cell;

    while (getline(ss, cell, ','))
    {
        totalFields++;
        if (cell.empty())
        {
            emptyFields++;
        }
    }

    // Considerar inválido se mais de 60% dos campos estiverem vazios
    if (totalFields == 0)
        return 0; // Evita divisão por zero
    double emptyRatio = static_cast<double>(emptyFields) / totalFields;
    return emptyRatio <= 0.6;
}

void generateCSV(const vector<FearTick> &fearTicks, const vector<Crypto> &cryptos, const map<string, vector<PriceHistory>> &priceMap)
{
    ofstream file("data/dataset.csv");
    file << "datetime,year,month,day,fear_api_alternative_me,fear_coinmarketcap";
    for (const auto &crypto : cryptos)
    {
        file << "," << crypto.symbol << "_min_value," << crypto.symbol << "_max_value";
    }
    file << "\n";

    unsigned long long rowsCount = 0;
    for (const auto &fearTick : fearTicks)
    {
        stringstream row;
        row << fearTick.year << ","
            << fearTick.month << ","
            << fearTick.day << ","
            << fearTick.fear_api_alternative_me << ","
            << fearTick.fear_coinmarketcap;

        auto it = priceMap.find(fearTick.datetimeStr);
        map<string, pair<cpp_dec_float, cpp_dec_float>> cryptoPrices;

        if (it != priceMap.end())
        {
            for (const auto &price : it->second)
            {
                cryptoPrices[price.symbol] = {price.min_value, price.max_value};
            }
        }

        for (const auto &crypto : cryptos)
        {
            auto priceIt = cryptoPrices.find(crypto.symbol);
            if (priceIt != cryptoPrices.end())
            {
                row << "," << priceIt->second.first << "," << priceIt->second.second;
            }
            else
            {
                row << ",,"; // Em caso de não encontrar o preço
            }
        }
        if (isRowValid(row))
        {
            file << row.str() << "\n";
            rowsCount++;
        }
    }
    std::cout << "CSV rows: " << rowsCount << std::endl;
}

map<string, string> loadEnvFile(const string &filename)
{
    ifstream file(filename);
    map<string, string> env;
    string line;

    while (getline(file, line))
    {
        size_t equalsPos = line.find('=');
        if (equalsPos != string::npos)
        {
            string key = line.substr(0, equalsPos);
            string value = line.substr(equalsPos + 1);
            env[key] = value;
        }
    }

    return env;
}

int main()
{
    try
    {
        map<string, string> env = loadEnvFile(".env");

        string host = "tcp://" + env["DATABASE_HOST"] + ":" + env["DATABASE_PORT"];
        string user = env["DATABASE_USER"];
        string pass = env["DATABASE_PASSWORD"];
        string dbName = env["DATABASE_DBNAME"];

        sql::mysql::MySQL_Driver *driver = sql::mysql::get_mysql_driver_instance();
        sql::Connection *con = driver->connect(host, user, pass);
        con->setSchema(dbName);

        vector<Crypto> cryptos;
        vector<FearTick> fearTicks;
        map<string, vector<PriceHistory>> priceMap;

        fetchCryptosAndPrices(con, cryptos, fearTicks, priceMap);
        generateCSV(fearTicks, cryptos, priceMap);

        cout << "CSV file generated successfully!" << endl;

        delete con;
        cryptos.clear();
        fearTicks.clear();
        priceMap.clear();
    }
    catch (sql::SQLException &e)
    {
        cout << "SQL error: " << e.what() << endl;
        cout << "MySQL error code: " << e.getErrorCode() << endl;
        cout << "SQLState: " << e.getSQLState() << endl;
    }

    return 0;
}
