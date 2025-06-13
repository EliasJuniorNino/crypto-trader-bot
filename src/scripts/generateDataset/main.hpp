#pragma once

#include <iostream>
#include <sqlite3.h>
#include <unordered_map>
#include <vector>
#include <string>
#include <fstream>
#include <curl/curl.h>

#include "../../services/BinanceVision.hpp"

class GenerateDataset
{
private:
    inline static std::string startDate;
    inline static std::string endDate;
    inline static sqlite3 *database;

    inline static std::vector<std::string> enabledCryptos;

public:
    static void Run(const std::string &start, const std::string &end, sqlite3 *db)
    {
        startDate = start;
        endDate = end;
        database = db;

        std::cout << "Generating dataset for " << startDate << " to " << endDate << std::endl;

        // Fetch enabled cryptos
        getEnabledCryptos();
        std::cout << "Processing crypto:";
        for (const auto &crypto : enabledCryptos)
        {
            std::cout << " " << crypto;
        }
        std::cout << std::endl;

        std::ofstream outFile("output.zip", std::ios::binary);

        std::string fileUrl = BinanceVision::getKlineFile("BTCUSDT", "1m", "2025-01");
        std::cout << fileUrl << std::endl;
    }

    static void getEnabledCryptos()
    {
        const char *sql = R"(
            SELECT c.symbol
            FROM cryptos c
            JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
            JOIN exchanges e ON ec.exchange_id = e.id
            WHERE LOWER(e.name) LIKE '%binance%'
            AND c.is_enabled = 1;
        )";

        sqlite3_stmt *stmt = nullptr;

        int rc = sqlite3_prepare_v2(database, sql, -1, &stmt, nullptr);
        if (rc != SQLITE_OK)
        {
            std::cerr << "Failed to prepare statement: " << sqlite3_errmsg(database) << std::endl;
            return;
        }

        enabledCryptos.clear();

        while ((rc = sqlite3_step(stmt)) == SQLITE_ROW)
        {
            const unsigned char *symbol = sqlite3_column_text(stmt, 0);
            if (symbol)
            {
                std::string symStr(reinterpret_cast<const char *>(symbol));
                enabledCryptos.push_back(symStr);
            }
        }

        if (rc != SQLITE_DONE)
        {
            std::cerr << "Error while executing statement: " << sqlite3_errmsg(database) << std::endl;
        }

        sqlite3_finalize(stmt);
    }
};
