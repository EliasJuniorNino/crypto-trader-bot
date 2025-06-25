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

func Main(initialDate time.Time, endDate time.Time, clearFiles bool) {
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

	isFullDatasetClear := false
	isHeaderAdded := false
	for i := initialDate; i.Before(time.Now().UTC()) && (i.Before(endDate) || i.Equal(endDate)); i = i.Add(24 * time.Hour) {
		yearStr := fixedCases(i.Year())
		monthStr := fixedCases(int(i.Month()))
		dayStr := fixedCases(i.Day())

		// Gera a data no formato YYYY-MM-DD
		dateStr := yearStr + "-" + monthStr + "-" + dayStr

		fear_api_alternative_me, err := getFearIndex(db, dateStr, "api.alternative.me")
		if err != nil {
			log.Printf("Fear index de alternative.me não encontrado para: %s", dateStr)
			return
		}

		fear_coinmarketcap, err := getFearIndex(db, dateStr, "CoinMarketCap")
		if err != nil {
			log.Printf("Fear index de coinmarketcap não encontrado para: %s", dateStr)
			return
		}

		if err := generateDatasetFile(i, cryptos, clearFiles, fear_api_alternative_me, fear_coinmarketcap); err != nil {
			return
		}

		if !isFullDatasetClear {
			if err := clearFinalDataset(); err != nil {
				log.Printf("Erro ao limpar o arquivo de dataset dataset_full.csv: %v", err)
				return
			}
			isFullDatasetClear = true
		}

		if err := mergeDatasetFile(i, &isHeaderAdded); err != nil {
			return
		}
	}
}

func mergeDatasetFile(currentTime time.Time, isHeaderAdded *bool) error {
	yearStr := fixedCases(currentTime.Year())
	monthStr := fixedCases(int(currentTime.Month()))
	dayStr := fixedCases(currentTime.Day())

	// Gera a data no formato YYYY-MM-DD
	dateStr := yearStr + "-" + monthStr + "-" + dayStr

	currentDatasetDir := filepath.Join(os.Getenv("DATASET_DIR"), "cache", dateStr)
	currentDatasetFilePath := filepath.Join(currentDatasetDir, "dataset-"+dateStr+".csv")

	finalDatasetDir := filepath.Join(os.Getenv("DATASET_DIR"))
	finalDatasetFilePath := filepath.Join(finalDatasetDir, "dataset_full.csv")

	// Abre o arquivo de origem
	sourceFile, err := os.Open(currentDatasetFilePath)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	// Abre (ou cria) o arquivo final em modo append
	destFile, err := os.OpenFile(finalDatasetFilePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer destFile.Close()

	scanner := bufio.NewScanner(sourceFile)
	writer := bufio.NewWriter(destFile)

	linesCount := 0
	isHeaderLine := true
	for scanner.Scan() {
		if isHeaderLine && *isHeaderAdded {
			isHeaderLine = false
			continue // ignora o cabeçalho
		}
		_, err := writer.WriteString(scanner.Text() + "\n")
		if err != nil {
			return err
		}
		*isHeaderAdded = true
		linesCount++
	}

	if err := scanner.Err(); err != nil {
		return err
	}

	log.Printf("%d Linhas de %s", linesCount, currentDatasetFilePath)

	return writer.Flush()
}

func generateDatasetFile(currentTime time.Time, cryptos []string, clearFiles bool, fear_api_alternative_me string, fear_coinmarketcap string) error {
	yearStr := fixedCases(currentTime.Year())
	monthStr := fixedCases(int(currentTime.Month()))
	dayStr := fixedCases(currentTime.Day())

	// Gera a data no formato YYYY-MM-DD
	dateStr := yearStr + "-" + monthStr + "-" + dayStr

	datasetDir := filepath.Join(os.Getenv("DATASET_DIR"), "cache", dateStr)
	datasetTempFilePath := filepath.Join(datasetDir, "dataset-"+dateStr+".tmp")
	datasetFilePath := filepath.Join(datasetDir, "dataset-"+dateStr+".csv")

	// Verifica se o arquivo de dataset já existe
	if !clearFiles {
		if _, err := os.Stat(datasetFilePath); err == nil {
			log.Printf("✅ Arquivo de dataset já existe: %s", datasetFilePath)
			return nil
		}
	}

	klineBasePath := os.Getenv("DATA_DIR") + "/data.binance.vision/data/spot/daily/klines"
	// Verifica se os arquivos CSV existem para cada criptomoeda
	for _, crypto := range cryptos {
		cryptoPair := crypto + "USDT"
		filePath := filepath.Join(klineBasePath, cryptoPair, "1m", "csv", cryptoPair+"-1m-"+dateStr+".csv")
		if _, err := os.Stat(filePath); os.IsNotExist(err) {
			log.Printf("Arquivo não encontrado: %s", filePath)
			return err
		}
	}

	log.Printf("Todos os arquivos encontrados para a data: %s", dateStr)

	// Cria diretório se não existir
	if _, err := os.Stat(datasetDir); os.IsNotExist(err) {
		if err := os.MkdirAll(datasetDir, 0755); err != nil {
			log.Printf("Erro ao criar diretório %s: %v", datasetDir, err)
			return err
		}
	}

	// Cria ou abre o arquivo de dataset para escrita (append ou novo)
	datasetFile, err := os.OpenFile(datasetTempFilePath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		log.Printf("Erro ao abrir ou criar o arquivo de dataset %s: %v", datasetTempFilePath, err)
		return err
	}
	defer func() {
		// Renomeia o arquivo de .tmp para .csv após a escrita bem-sucedida
		if err := os.Rename(datasetTempFilePath, datasetFilePath); err != nil {
			log.Printf("Erro ao renomear o arquivo de dataset: %v", err)
		}
	}()
	defer datasetFile.Close()

	// Cria um writer para o arquivo de dataset
	datasetWriter := bufio.NewWriter(datasetFile)
	defer datasetWriter.Flush()

	// Limpa o arquivo de dataset se já existir
	if err := datasetFile.Truncate(0); err != nil {
		log.Printf("Erro ao limpar o arquivo de dataset %s: %v", datasetFilePath, err)
		return err
	}

	// Cria o cabeçalho do dataset
	datasetHeader := []string{"OpenTime", "fear_api_alternative_me", "fear_coinmarketcap"}

	// Adiciona coluna no cabeçalho para cada criptomoeda
	for _, crypto := range cryptos {
		datasetHeader = append(
			datasetHeader,
			crypto+"Open",
			crypto+"High",
			crypto+"Low",
			crypto+"Close",
			crypto+"Volume",
			crypto+"QuoteAssetVolume",
			crypto+"NumberOfTrades",
			crypto+"TakerBuyBaseVolume",
			crypto+"TakerBuyQuoteVolume",
		)
	}

	// Grava o cabeçalho no arquivo de dataset
	lineStr := strings.Join(datasetHeader, ",") + "\n"
	if _, err := datasetWriter.WriteString(lineStr); err != nil {
		log.Printf("Erro ao escrever no arquivo de dataset: %v", err)
		return err
	}

	// Lê cada arquivo CSV e extrai as linhas necessárias
	for lineNumber := 0; lineNumber < 1440; lineNumber++ {
		datasetLine := []string{fear_api_alternative_me, fear_coinmarketcap}

		var openTime int64 = 0
		for _, crypto := range cryptos {
			cryptoPair := crypto + "USDT"
			filePath := filepath.Join(klineBasePath, cryptoPair, "1m", "csv", cryptoPair+"-1m-"+dateStr+".csv")

			kline, err := getFileLine(filePath, lineNumber)
			if err != nil {
				log.Printf("Erro ao kline para a linha %d do arquivo %s: %v", lineNumber, filePath, err)
				return err
			}

			// Grava o timestamp de abertura apenas para a primeira coluna
			if openTime == 0 {
				openTime = kline.OpenTime
			}

			datasetLine = append(datasetLine,
				kline.Open,
				kline.High,
				kline.Low,
				kline.Close,
				kline.Volume,
				kline.QuoteAssetVolume,
				strconv.Itoa(kline.NumberOfTrades),
				kline.TakerBuyBaseVolume,
				kline.TakerBuyQuoteVolume,
			)
		}

		// Só adiciona ao dataset se tiver conteúdo
		if len(datasetLine) > 0 {
			// Adiciona o timestamp de abertura na primeira posição
			datasetLine = append([]string{strconv.FormatInt(openTime, 10)}, datasetLine...)

			// Separa os valores por vírgula e adiciona uma nova linha
			lineStr := strings.Join(datasetLine, ",") + "\n"

			// Escreve a linha no arquivo de dataset
			if _, err := datasetWriter.WriteString(lineStr); err != nil {
				log.Printf("Erro ao escrever no arquivo de dataset: %v", err)
				return err
			}
			log.Printf("Linha %d adicionada ao dataset para a data %s", lineNumber, dateStr)
		}
	}

	log.Printf("Dataset gerado com sucesso em: %s", datasetFilePath)
	return nil
}

func getFearIndex(db *sql.DB, dateStr string, sourceStr string) (string, error) {
	query := `
        SELECT value
        FROM fear_index
        WHERE date LIKE ? AND source = ?;
    `
	var fearIndex float64
	err := db.QueryRow(query, "%"+dateStr+"%", sourceStr).Scan(&fearIndex)
	if err != nil {
		return "0", err
	}
	return fmt.Sprintf("%v", fearIndex), nil
}

func getFileLine(filePath string, lineNumber int) (*models.BinanceKline, error) {
	// Abre arquivo CSV para leitura
	file, err := os.Open(filePath)
	if err != nil {
		log.Printf("Erro ao abrir o arquivo %s: %v", filePath, err)
		return nil, err
	}
	defer file.Close()

	// Cria um scanner para ler o arquivo linha por linha
	scanner := bufio.NewScanner(file)
	currentLineNumber := 1
	for currentLineNumber < lineNumber && scanner.Scan() {
		currentLineNumber++
	}

	// Agora o scanner está posicionado na linha desejada (ou no final do arquivo)
	if scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) >= 12 {
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
			return &kline, nil
		} else {
			return nil, fmt.Errorf("linha %d do arquivo %s não possui colunas suficientes", lineNumber, filePath)
		}
	}
	return nil, fmt.Errorf("não foi possível ler a linha %d do arquivo %s", lineNumber, filePath)
}

func clearFinalDataset() error {
	finalDatasetDir := filepath.Join(os.Getenv("DATASET_DIR"))
	finalDatasetFilePath := filepath.Join(finalDatasetDir, "dataset_full.csv")

	// Cria ou abre o arquivo de dataset para escrita (append ou novo)
	datasetFile, err := os.OpenFile(finalDatasetFilePath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		log.Printf("Erro ao abrir ou criar o arquivo de dataset %s: %v", finalDatasetFilePath, err)
		return err
	}
	defer datasetFile.Close()

	// Cria um writer para o arquivo de dataset
	datasetWriter := bufio.NewWriter(datasetFile)
	defer datasetWriter.Flush()

	// Limpa o arquivo de dataset se já existir
	if err := datasetFile.Truncate(0); err != nil {
		log.Printf("Erro ao limpar o arquivo de dataset %s: %v", finalDatasetFilePath, err)
		return err
	}

	return nil
}

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
