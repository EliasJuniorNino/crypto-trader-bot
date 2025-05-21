package scripts

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

func GetBinanceCurrentDayCryptos() {
	// Abrir conexão com o banco de dados SQLite
	db, err := sql.Open("sqlite3", "database/database.db")
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	defer db.Close()

	// Exemplo: Buscar criptomoedas da Binance habilitadas
	cryptos, err := fetchCryptos(db)
	if err != nil {
		log.Printf("Erro ao buscar criptomoedas: %v", err)
	} else {
		log.Printf("Criptomoedas encontradas: %v", cryptos)
	}

	// Exemplo: Inserir histórico de preços
	priceHistory := []PriceHistory{
		{
			Date:                    time.Now(),
			Price:                   50000.0,
			CryptoID:                1,
			ExchangeID:              1,
			OpenTime:                time.Now().Unix(),
			OpenPrice:               49500.0,
			HighPrice:               50500.0,
			LowPrice:                49000.0,
			ClosePrice:              50000.0,
			Volume:                  123.456,
			CloseTime:               time.Now().Add(time.Minute * 1).Unix(),
			BaseAssetVolume:         123.456,
			NumberOfTrades:          100,
			TakerBuyVolume:          60.0,
			TakerBuyBaseAssetVolume: 60.0,
		},
		// Adicione mais registros conforme necessário
	}

	err = savePriceHistoryToCSV(db, "BTC", priceHistory)
	if err != nil {
		log.Printf("Erro ao inserir histórico de preços: %v", err)
	} else {
		log.Println("Histórico de preços inserido com sucesso.")
	}
}

func savePriceHistoryToCSV(db *sql.DB, symbol string, priceHistory []PriceHistory) error {
	// Verifica se o diretório existe, se não existir, cria
	file, err := os.Create("data/last_history/1m/{%s}.csv")
	if err != nil {
		return err
	}
	defer file.Close()

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

// PriceHistory representa um registro de histórico de preços
type PriceHistory struct {
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
