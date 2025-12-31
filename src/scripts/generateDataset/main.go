package generateDataset

import (
	"app/src/database"
	"app/src/models"
	"bufio"
	"database/sql"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
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

	// Gera dataset para cada dia entre a data inicial e a data final
	var wg sync.WaitGroup
	maxGoroutines := runtime.NumCPU() * 2
	sem := make(chan struct{}, maxGoroutines)
	for i := initialDate; i.Before(time.Now().UTC()) && (i.Before(endDate) || i.Equal(endDate)); i = i.Add(24 * time.Hour) {
		yearStr := fixedCases(i.Year())
		monthStr := fixedCases(int(i.Month()))
		dayStr := fixedCases(i.Day())

		// Gera a data no formato YYYY-MM-DD
		wg.Add(1)
		sem <- struct{}{} // bloquear aqui se já tiver maxGoroutines em execução
		go func(index time.Time, dateStr string) {
			defer wg.Done()
			defer func() { <-sem }()
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

			if err := generateDatasetFile(index, cryptos, clearFiles, fear_api_alternative_me, fear_coinmarketcap); err != nil {
				return
			}
		}(i, yearStr+"-"+monthStr+"-"+dayStr)
	}
	wg.Wait()

	// Gera o arquivo final unificado entre a data inicial e a data final
	isFullDatasetClear := false
	isHeaderAdded := false
	for i := initialDate; i.Before(time.Now().UTC()) && (i.Before(endDate) || i.Equal(endDate)); i = i.Add(24 * time.Hour) {
		if !isFullDatasetClear {
			if err := clearFinalDataset(); err != nil {
				log.Printf("Erro ao limpar o arquivo de dataset dataset_full.csv: %v", err)
				return
			}
			isFullDatasetClear = true
		}

		if err := mergeDatasetFile(i, &isHeaderAdded); err != nil {
			log.Printf("Erro ao adicionar conteudo ao o arquivo de dataset dataset_full.csv: %v", err)
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

	sourceFile.Seek(0, 0)
	scanner := bufio.NewScanner(sourceFile)
	writer := bufio.NewWriter(destFile)

	linesCount := 0
	isHeaderLine := true

	// Move scanner para inicio
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

	klineBasePath := filepath.Join(os.Getenv("DATA_DIR"), "data.binance.vision/data/spot/daily/klines")

	// Pre-carrega todos os klines para a memória (aprox 1440 por crypto)
	// Mapa: crypto -> []models.BinanceKline
	allKlines := make(map[string][]*models.BinanceKline)

	for _, crypto := range cryptos {
		cryptoPair := crypto + "USDT"
		filePath := filepath.Join(klineBasePath, cryptoPair, "1m", "csv", cryptoPair+"-1m-"+dateStr+".csv")

		klines, err := readAllKlines(filePath)
		if err != nil {
			log.Printf("Arquivo não encontrado ou erro ao ler: %s", filePath)
			return err
		}
		if len(klines) < 1440 {
			log.Printf("Aviso: Arquivo %s tem apenas %d linhas (esperado 1440)", filePath, len(klines))
		}
		allKlines[crypto] = klines
	}

	log.Printf("Todos os arquivos carregados para a data: %s", dateStr)

	// Cria diretório se não existir
	if err := os.MkdirAll(datasetDir, 0755); err != nil {
		log.Printf("Erro ao criar diretório %s: %v", datasetDir, err)
		return err
	}

	// Cria ou abre o arquivo de dataset para escrita
	datasetFile, err := os.Create(datasetTempFilePath)
	if err != nil {
		log.Printf("Erro ao criar o arquivo temporário %s: %v", datasetTempFilePath, err)
		return err
	}
	defer func() {
		datasetFile.Close()
		// Renomeia o arquivo de .tmp para .csv após a escrita bem-sucedida
		if err := os.Rename(datasetTempFilePath, datasetFilePath); err != nil && !os.IsNotExist(err) {
			log.Printf("Erro ao renomear o arquivo de dataset: %v", err)
		}
	}()

	// Cria um writer para o arquivo de dataset
	datasetWriter := bufio.NewWriter(datasetFile)

	// Cria o cabeçalho do dataset
	datasetHeader := []string{"OpenTime", "fear_api_alternative_me", "fear_coinmarketcap"}
	for _, crypto := range cryptos {
		datasetHeader = append(datasetHeader,
			crypto+"_Open",
			crypto+"_High",
			crypto+"_Low",
			crypto+"_Close",
			crypto+"_Volume",
			crypto+"_QuoteAssetVolume",
			crypto+"_NumberOfTrades",
			crypto+"_TakerBuyBaseVolume",
			crypto+"_TakerBuyQuoteVolume",
		)
	}

	// Grava o cabeçalho
	if _, err := datasetWriter.WriteString(strings.Join(datasetHeader, ",") + "\n"); err != nil {
		return err
	}

	// Processa cada minuto (1440 por dia)
	for i := 0; i < 1440; i++ {
		var openTime int64
		datasetLine := []string{fear_api_alternative_me, fear_coinmarketcap}

		for _, crypto := range cryptos {
			klines := allKlines[crypto]
			var k *models.BinanceKline
			if i < len(klines) {
				k = klines[i]
			} else {
				// Fallback para kline vazio se faltar dados
				k = &models.BinanceKline{}
			}

			if openTime == 0 && k.OpenTime != 0 {
				openTime = k.OpenTime
			}

			datasetLine = append(datasetLine,
				k.Open,
				k.High,
				k.Low,
				k.Close,
				k.Volume,
				k.QuoteAssetVolume,
				strconv.Itoa(k.NumberOfTrades),
				k.TakerBuyBaseVolume,
				k.TakerBuyQuoteVolume,
			)
		}

		// Prepend OpenTime
		finalLine := append([]string{strconv.FormatInt(openTime, 10)}, datasetLine...)
		if _, err := datasetWriter.WriteString(strings.Join(finalLine, ",") + "\n"); err != nil {
			return err
		}
	}

	if err := datasetWriter.Flush(); err != nil {
		return err
	}

	log.Printf("Dataset gerado com sucesso em: %s", datasetFilePath)
	return nil
}

func readAllKlines(filePath string) ([]*models.BinanceKline, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var klines []*models.BinanceKline
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) >= 12 {
			klines = append(klines, &models.BinanceKline{
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
			})
		}
	}
	return klines, scanner.Err()
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
	return strconv.FormatFloat(fearIndex, 'f', -1, 64), nil
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
