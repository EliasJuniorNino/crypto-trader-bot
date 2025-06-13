#include <string>
#include <cstdint>

// Representa um candle da API da Binance
struct BinanceKline
{
    int64_t OpenTime;
    std::string Open;
    std::string High;
    std::string Low;
    std::string Close;
    std::string Volume;
    int64_t CloseTime;
    std::string QuoteAssetVolume;
    int NumberOfTrades;
    std::string TakerBuyBaseVolume;
    std::string TakerBuyQuoteVolume;
    std::string Ignore; // geralmente zero
};

// Representa um histórico de preços já processado
struct BinancePriceHistory
{
    std::string Date;
    double Price;
    int CryptoID;
    int ExchangeID;
    int64_t OpenTime;
    double OpenPrice;
    double HighPrice;
    double LowPrice;
    double ClosePrice;
    double Volume;
    int64_t CloseTime;
    double BaseAssetVolume;
    int NumberOfTrades;
    double TakerBuyVolume;
    double TakerBuyBaseAssetVolume;
};
