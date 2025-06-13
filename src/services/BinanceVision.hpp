#pragma once

#include <curl/curl.h>
#include <stdexcept>
#include <sstream>
#include <fstream>
#include <memory>
#include <string>
#include <filesystem>

#if defined(__has_include)
#if __has_include(<format>) && __cplusplus >= 202002L
#include <format>
#define HAS_STD_FORMAT 1
#else
#define HAS_STD_FORMAT 0
#endif
#else
#define HAS_STD_FORMAT 0
#endif

namespace fs = std::filesystem;

class BinanceVision
{
private:
    // Callback para escrever diretamente no arquivo
    static size_t WriteToFileCallback(void *contents, size_t size, size_t nmemb, void *userp)
    {
        std::ofstream *ofs = static_cast<std::ofstream *>(userp);
        ofs->write(static_cast<char *>(contents), size * nmemb);
        return size * nmemb;
    }

public:
    // Salva o .zip na pasta especificada e retorna o caminho completo
    static std::string getKlineFile(const std::string &pair, const std::string &interval, const std::string &dateTimeStr, const std::string &outputDir = "data")
    {
        std::string filename = pair + "-" + interval + "-" + dateTimeStr + ".zip";
        std::string url = "https://data.binance.vision/data/spot/monthly/klines/" + pair + "/" + interval + "/" + filename;
        std::string filepath = outputDir + "/" + filename;

        // Cria diretório se não existir
        fs::create_directories(outputDir);

        std::ofstream ofs(filepath, std::ios::binary);
        if (!ofs.is_open())
        {
            throw std::runtime_error("Erro ao abrir o arquivo para escrita: " + filepath);
        }

        auto curl = std::unique_ptr<CURL, decltype(&curl_easy_cleanup)>(curl_easy_init(), curl_easy_cleanup);
        if (!curl)
        {
            throw std::runtime_error("Falha ao inicializar CURL");
        }

        curl_easy_setopt(curl.get(), CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl.get(), CURLOPT_WRITEFUNCTION, WriteToFileCallback);
        curl_easy_setopt(curl.get(), CURLOPT_WRITEDATA, &ofs);
        curl_easy_setopt(curl.get(), CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl.get(), CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl.get(), CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl.get(), CURLOPT_TIMEOUT, 30L);
        curl_easy_setopt(curl.get(), CURLOPT_USERAGENT, "BinanceVisionClient/1.0");

        CURLcode res = curl_easy_perform(curl.get());
        ofs.close();

        if (res != CURLE_OK)
        {
#if HAS_STD_FORMAT
            throw std::runtime_error(std::format("Falha no download CURL: {}", curl_easy_strerror(res)));
#else
            std::ostringstream oss;
            oss << "Falha no download CURL: " << curl_easy_strerror(res);
            throw std::runtime_error(oss.str());
#endif
        }

        long httpCode = 0;
        curl_easy_getinfo(curl.get(), CURLINFO_RESPONSE_CODE, &httpCode);
        if (httpCode >= 400)
        {
#if HAS_STD_FORMAT
            throw std::runtime_error(std::format("Erro HTTP {} ao baixar '{}'", httpCode, url));
#else
            std::ostringstream oss;
            oss << "Erro HTTP " << httpCode << " ao baixar '" << url << "'";
            throw std::runtime_error(oss.str());
#endif
        }

        return filepath;
    }
};
