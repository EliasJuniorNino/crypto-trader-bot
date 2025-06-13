#pragma once

#include <iostream>
#include <sqlite3.h>
#include <unordered_map>

#include "utils/config.hpp"
#include "scripts/generateDataset/main.hpp"

class Application
{
public:
    static void Run(std::unordered_map<std::string, std::string> params, sqlite3 *db)
    {
        if (params.empty() || !params["-h"].empty())
        {
            printHelp();
            return;
        }

        if (!params["-GetFearCoinmarketcap"].empty())
        {
            std::cout << "GetFearCoinmarketcap" << std::endl;
        }

        if (!params["-GetFearAlternativeMe"].empty())
        {
            std::cout << "GetFearAlternativeMe" << std::endl;
        }

        if (!params["-GenerateDataset"].empty())
        {
            GenerateDataset::Run(params["-start"], params["-end"], db);
        }
    }

    static void printHelp()
    {
        const std::string helpText = R"(
📊 CRYPTOTRADER - CLI (sem interação)
=============================================================
Uso:
  CryptoTrader [OPÇÃO] [FLAGS OPCIONAIS]

Opções:
  -h                            → Exibe este menu
  -GetFearCoinmarketcap         → Executa GetFearCoinmarketcap
  -GetFearAlternativeMe         → Executa GetFearAlternativeMe
  -GenerateDataset              → Executa GenerateDataset 
                                    (-start 2024-01-01 -end 2024-12-31)
        
Exemplo:
  ./CryptoTrader -GenerateDataset -start 2024-01-01 -end 2024-12-31

=============================================================
)";
        std::cout << helpText;
    }
};
