package generateDataset

import (
	"app/src/database"
	"app/src/models"
	"bufio"
	"database/sql"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// busca criptomoedas da binance habilitadas
func fetchEnabledCryptos(db *sql.DB) ([]string, error) {
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

func Main(initialDate time.Time, endDate time.Time) {
	// Conexão com o banco de dados
	db, err := database.ConnectDatabase()
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	defer db.Close()

	// Busca as criptomoedas habilitadas
	cryptos, err := fetchEnabledCryptos(db)
	if err != nil {
		panic(err)
	}

	for i := initialDate; i.Before(time.Now().UTC()) && (i.Before(endDate) || i.Equal(endDate)); i = i.Add(24 * time.Hour) {
		yearStr := fixedCases(i.Year())
		monthStr := fixedCases(int(i.Month()))
		dayStr := fixedCases(i.Day())

		dateStr := yearStr + "-" + monthStr + "-" + dayStr
		for _, crypto := range cryptos {
			cryptoPair := crypto + "USDT"
			filePath := filepath.Join("data", "binance_data", cryptoPair, "1m", "csv", cryptoPair+"-1m-"+dateStr+".csv")
			if _, err := os.Stat(filePath); os.IsNotExist(err) {
				log.Printf("Arquivo não encontrado: %s", filePath)
				return
			}
		}

		log.Printf("Todos os arquivos encontrados para a data: %s", dateStr)

		//datasetLine := [][]string{}

		for _, crypto := range cryptos {
			cryptoPair := crypto + "USDT"
			filePath := filepath.Join("data", "binance_data", cryptoPair, "1m", "csv", cryptoPair+"-1m-"+dateStr+".csv")

			// Abre arquivo CSV para leitura
			file, err := os.Open(filePath)
			if err != nil {
				log.Printf("Erro ao abrir o arquivo %s: %v", filePath, err)
				continue
			}
			defer file.Close()

			// Cria um scanner para ler o arquivo linha por linha
			scanner := bufio.NewScanner(file)
			// Ignora a primeira linha (cabeçalho)
			if scanner.Scan() {
				// Cabeçalho ignorado
			}

			lineNumber := 1
			for scanner.Scan() && lineNumber < 1440 {
				line := scanner.Text()

				// Carrega as colunas em model.BinanceKline
				fields := strings.Split(line, ",")
				kline := models.BinanceKline{
					OpenTime:            toInt64(fields[0]),
					Open:                fields[1],
					High:                fields[2],
					Low:                 fields[3],
					Close:               fields[4],
					Volume:              fields[5],
					CloseTime:           toInt64(fields[6]),
					QuoteAssetVolume:    fields[7],
					NumberOfTrades:      toInt(fields[8]),
					TakerBuyBaseVolume:  fields[9],
					TakerBuyQuoteVolume: fields[10],
					Ignore:              fields[11],
				}
				fmt.Printf("Kline: %+v\n", kline)

				lineNumber++
			}
		}
	}
}

func fixedCases(value int) string {
	if value < 10 {
		return "0" + strconv.Itoa(value)
	}
	return strconv.Itoa(value)
}

func toInt(value string) int {
	parsedValue, err := strconv.Atoi(value)
	if err != nil {
		log.Printf("Erro ao converter %s para int: %v", value, err)
		return 0
	}
	return parsedValue
}

func toInt64(value string) int64 {
	parsedValue, err := strconv.ParseInt(value, 10, 64)
	if err != nil {
		log.Printf("Erro ao converter %s para int64: %v", value, err)
		return 0
	}
	return parsedValue
}
