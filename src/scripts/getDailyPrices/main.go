package getDailyPrices

import (
	"app/src/database"
	"app/src/models"
	"app/src/utils"
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

func Main() {
	// Abrir conexão com o banco de dados SQLite
	db, err := database.ConnectDatabase()
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	defer db.Close()

	// Exemplo: Buscar criptomoedas da Binance habilitadas
	cryptos, err := fetchCryptos(db)
	if err != nil {
		log.Printf("Erro ao buscar criptomoedas: %v", err)
	} else {
		log.Printf("%d Criptomoedas encontradas!", len(cryptos))
	}

	priceHistoryMap := make(map[string][]models.BinancePriceHistory)

	start := utils.StartOfCurrentDayUTC()

	for i := start; i.Add(time.Hour).Before(time.Now().UTC()); i = i.Add(time.Hour) {
		startTime := i
		endTime := i.Add(time.Hour)

		for _, symbol := range cryptos {
			priceHistoryList := priceHistoryMap[symbol]

			klines, err := fetchBinanceKlines(symbol, startTime, endTime)
			if err != nil {
				log.Printf("Erro ao buscar klines da Binance para %s: %v", symbol, err)
				continue
			}

			for _, kline := range klines {
				date := time.UnixMilli(kline.CloseTime)
				date = date.Truncate(time.Minute)
				openPrice, _ := strconv.ParseFloat(kline.Open, 64)
				highPrice, _ := strconv.ParseFloat(kline.High, 64)
				lowPrice, _ := strconv.ParseFloat(kline.Low, 64)
				closePrice, _ := strconv.ParseFloat(kline.Close, 64)
				volume, _ := strconv.ParseFloat(kline.Volume, 64)
				baseVolume, _ := strconv.ParseFloat(kline.QuoteAssetVolume, 64)
				takerBuyVolume, _ := strconv.ParseFloat(kline.TakerBuyQuoteVolume, 64)
				takerBuyBaseVolume, _ := strconv.ParseFloat(kline.TakerBuyBaseVolume, 64)

				priceHistoryList = append(priceHistoryList, models.BinancePriceHistory{
					Date:                    date, // ou time.Now() se preferir
					Price:                   closePrice,
					CryptoID:                1, // ajuste conforme necessário
					ExchangeID:              1, // ajuste conforme necessário
					OpenTime:                kline.OpenTime,
					OpenPrice:               openPrice,
					HighPrice:               highPrice,
					LowPrice:                lowPrice,
					ClosePrice:              closePrice,
					Volume:                  volume,
					CloseTime:               kline.CloseTime,
					BaseAssetVolume:         baseVolume,
					NumberOfTrades:          kline.NumberOfTrades,
					TakerBuyVolume:          takerBuyVolume,
					TakerBuyBaseAssetVolume: takerBuyBaseVolume,
				})
			}

			priceHistoryMap[symbol] = priceHistoryList
		}
		log.Printf("Klines entre %s e %s -> OK", startTime.Format(time.RFC3339), endTime.Format(time.RFC3339))
		log.Printf("UTC Agora: %s", time.Now().UTC().Format(time.RFC3339))
	}

	for _, symbol := range cryptos {
		priceHistoryList := priceHistoryMap[symbol]
		err = savePriceHistoryToCSV(symbol, priceHistoryList)
		if err != nil {
			log.Printf("Erro ao inserir histórico de preços: %v", err)
		}
	}
}

// Retorna o histórico de preços da API da Binance para a criptomoeda symbol
func fetchBinanceKlines(symbol string, startTime time.Time, endTime time.Time) ([]models.BinanceKline, error) {
	// Define a URL da API para buscar o histórico de Klines (ex: 1 minuto)
	symbolParam := symbol + "USDT"

	startTimeStr := fmt.Sprintf("%d", startTime.UnixMilli())
	endTimeStr := fmt.Sprintf("%d", endTime.UnixMilli())

	baseURL := "https://api.binance.com/api/v3/klines"
	u, _ := url.Parse(baseURL)

	query := url.Values{}
	query.Set("symbol", symbolParam)
	query.Set("interval", "1m")
	query.Set("limit", "60")
	query.Set("startTime", startTimeStr)
	query.Set("endTime", endTimeStr)

	u.RawQuery = query.Encode()
	finalURL := u.String()

	// Faz a requisição HTTP
	resp, err := http.Get(finalURL)
	if err != nil {
		return nil, fmt.Errorf("erro ao fazer requisição para Binance: %w", err)
	}
	defer resp.Body.Close()

	// Verifica se o status HTTP é 200
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("resposta inválida da Binance: %s", resp.Status)
	}

	// Lê o corpo da resposta
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("erro ao ler corpo da resposta: %w", err)
	}

	// Decodifica o JSON em um array genérico
	var rawKlines [][]any
	if err := json.Unmarshal(body, &rawKlines); err != nil {
		return nil, fmt.Errorf("erro ao decodificar JSON: %w", err)
	}

	var klines []models.BinanceKline
	for _, k := range rawKlines {
		if len(k) < 12 {
			continue
		}
		openTime, _ := toInt64(k[0])
		open, _ := toString(k[1])
		high, _ := toString(k[2])
		low, _ := toString(k[3])
		closeVal, _ := toString(k[4])
		volume, _ := toString(k[5])
		closeTime, _ := toInt64(k[6])
		quoteAssetVolume, _ := toString(k[7])
		numberOfTrades, _ := toInt(k[8])
		takerBuyBaseVolume, _ := toString(k[9])
		takerBuyQuoteVolume, _ := toString(k[10])
		// ignore k[11] (unused)

		klines = append(klines, models.BinanceKline{
			OpenTime:            openTime,
			Open:                open,
			High:                high,
			Low:                 low,
			Close:               closeVal,
			Volume:              volume,
			CloseTime:           closeTime,
			QuoteAssetVolume:    quoteAssetVolume,
			NumberOfTrades:      numberOfTrades,
			TakerBuyBaseVolume:  takerBuyBaseVolume,
			TakerBuyQuoteVolume: takerBuyQuoteVolume,
		})
	}

	return klines, nil
}

func savePriceHistoryToCSV(symbol string, priceHistory []models.BinancePriceHistory) error {
	dir_path := "data/last_history/1m"

	// Verifica se o diretório existe
	if _, err := os.Stat(dir_path); os.IsNotExist(err) {
		log.Printf("Diretorio não existe: %v", err)

		// Cria o diretório
		err := os.MkdirAll(dir_path, os.ModePerm)
		if err != nil {
			return fmt.Errorf("erro ao criar diretório: %v", err)
		}
	}

	// Cria o arquivo CSV abrindo para escrita
	file, err := os.Create(fmt.Sprintf("%s/%s.csv", dir_path, symbol))
	if err != nil {
		return fmt.Errorf("erro ao criar arquivo CSV: %v", err)
	}
	defer file.Close()

	// Cria um writer CSV
	writer := csv.NewWriter(file)
	defer writer.Flush()

	for _, record := range priceHistory {
		err := writer.Write([]string{
			record.Date.Format(time.RFC3339),
			fmt.Sprintf("%.2f", record.Price),
			fmt.Sprintf("%d", record.CryptoID),
			fmt.Sprintf("%d", record.ExchangeID),
			fmt.Sprintf("%d", record.OpenTime),
			fmt.Sprintf("%.2f", record.OpenPrice),
			fmt.Sprintf("%.2f", record.HighPrice),
			fmt.Sprintf("%.2f", record.LowPrice),
			fmt.Sprintf("%.2f", record.ClosePrice),
			fmt.Sprintf("%.2f", record.Volume),
			fmt.Sprintf("%d", record.CloseTime),
			fmt.Sprintf("%.2f", record.BaseAssetVolume),
			fmt.Sprintf("%d", record.NumberOfTrades),
			fmt.Sprintf("%.2f", record.TakerBuyVolume),
			fmt.Sprintf("%.2f", record.TakerBuyBaseAssetVolume),
		})
		if err != nil {
			return err
		}
	}

	return nil
}

// busca criptomoedas da binance habilitadas
func fetchCryptos(db *sql.DB) ([]string, error) {
	query := `
        SELECT c.symbol
        FROM cryptos c
        JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
        JOIN exchanges e ON ec.exchange_id = e.id
        WHERE LOWER(e.name) LIKE '%binance%'
        AND c.is_enabled = 1;
    `
	rows, err := db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []string
	for rows.Next() {
		var symbol string
		if err := rows.Scan(&symbol); err != nil {
			return nil, err
		}
		symbols = append(symbols, symbol)
	}
	return symbols, nil
}

func toInt64(val interface{}) (int64, error) {
	switch v := val.(type) {
	case float64:
		return int64(v), nil
	case string:
		return strconv.ParseInt(v, 10, 64)
	default:
		return 0, fmt.Errorf("cannot convert %T to int64", val)
	}
}

func toString(val interface{}) (string, error) {
	switch v := val.(type) {
	case string:
		return v, nil
	case float64:
		return fmt.Sprintf("%f", v), nil
	case int:
		return strconv.Itoa(v), nil
	default:
		return "", fmt.Errorf("cannot convert %T to string", val)
	}
}

func toInt(val interface{}) (int, error) {
	switch v := val.(type) {
	case float64:
		return int(v), nil
	case string:
		i, err := strconv.Atoi(v)
		return i, err
	default:
		return 0, fmt.Errorf("cannot convert %T to int", val)
	}
}
