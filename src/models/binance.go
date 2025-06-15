package models

import "time"

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

type BinancePriceHistory struct {
	Date                    time.Time
	Price                   float64
	CryptoID                int
	ExchangeID              int
	OpenTime                int64
	OpenPrice               float64
	HighPrice               float64
	LowPrice                float64
	ClosePrice              float64
	Volume                  float64
	CloseTime               int64
	BaseAssetVolume         float64
	NumberOfTrades          int
	TakerBuyVolume          float64
	TakerBuyBaseAssetVolume float64
}
