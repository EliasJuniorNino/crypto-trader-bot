package models

// BinanceKline representa um candle da API da Binance
type BinanceKline struct {
	OpenTime            int64
	Open                string
	High                string
	Low                 string
	Close               string
	Volume              string
	CloseTime           int64
	QuoteAssetVolume    string
	NumberOfTrades      int
	TakerBuyBaseVolume  string
	TakerBuyQuoteVolume string
	Ignore              string // geralmente zero
}
