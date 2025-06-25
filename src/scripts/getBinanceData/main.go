package getBinanceData

import (
	"app/src/database"
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	_ "github.com/joho/godotenv/autoload"
	_ "github.com/mattn/go-sqlite3"
)

// Estrutura para armazenar progresso
type Progress struct {
	LastProcessedDate string `json:"last_processed_date,omitempty"`
	StartedDate       string `json:"started_date,omitempty"`
}

// Estrutura para criptomoedas habilitadas
type EnabledCrypto struct {
	ID         int
	Symbol     string
	ExchangeID int
	IsEnabled  int
}

func Main(isAllCryptosEnabled bool) {
	// Configurar logging
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("INFO: ")

	var cryptos []EnabledCrypto
	var err error
	if isAllCryptosEnabled {
		cryptos, err = getAllCryptos()
	} else {
		cryptos, err = getEnabledCryptos()
	}
	if err != nil {
		log.Printf("Erro ao obter criptos: %v", err)
		return
	}

	if len(cryptos) > 0 {
		// Criar slice de pares de trading
		var pairs []string
		for _, crypto := range cryptos {
			pairs = append(pairs, fmt.Sprintf("%sUSDT", crypto.Symbol))
		}

		// Pega data inicial da última vez
		startedDate := loadStartedDate()
		today := time.Now()
		oneDayAgo := today.AddDate(0, 0, -1)

		// Verifica se a data de início é menor que ontem
		if startedDate.Before(oneDayAgo) {
			log.Printf("📅 Recuperando dados recentes até: %s", startedDate.Format("2006-01-02"))
			err := downloadAndExtractKlines(
				pairs,
				"1m", // Intervalo de 1 minuto
				0,
				startedDate.Format("2006-01-02"),
				oneDayAgo.Format("2006-01-02"),
				os.Getenv("DATA_DIR"),
			)
			if err != nil {
				log.Printf("Erro ao baixar dados recentes: %v", err)
			}
		}

		// Segunda parte: histórico completo até 2017
		lastProcessed := loadLastProcessedDate()
		err := downloadAndExtractKlines(
			pairs,
			"1m", // Intervalo de 1 minuto
			0,
			"2017-01-01",
			lastProcessed.Format("2006-01-02"),
			os.Getenv("DATA_DIR"),
		)
		if err != nil {
			log.Printf("Erro ao baixar dados históricos: %v", err)
		}
	} else {
		log.Println("Nenhuma criptomoeda habilitada encontrada.")
	}
}

// Obter criptomoedas habilitadas
func getEnabledCryptos() ([]EnabledCrypto, error) {
	db, err := database.ConnectDatabase()
	if err != nil {
		return nil, err
	}
	defer db.Close()

	rows, err := db.Query(`
		SELECT c.id, c.symbol, e.id AS exchange_id, c.is_enabled
		FROM cryptos c
		JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
		JOIN exchanges e ON ec.exchange_id = e.id
		WHERE LOWER(e.name) LIKE '%binance%'
		AND c.is_enabled = 1;
	`)
	if err != nil {
		return nil, fmt.Errorf("erro ao buscar criptos: %w", err)
	}
	defer rows.Close()

	var cryptos []EnabledCrypto
	for rows.Next() {
		var crypto EnabledCrypto
		if err := rows.Scan(&crypto.ID, &crypto.Symbol, &crypto.ExchangeID, &crypto.IsEnabled); err != nil {
			return nil, fmt.Errorf("erro ao ler linha: %w", err)
		}
		cryptos = append(cryptos, crypto)
	}

	return cryptos, nil
}

// Obter todas criptomoedas
func getAllCryptos() ([]EnabledCrypto, error) {
	db, err := database.ConnectDatabase()
	if err != nil {
		return nil, err
	}
	defer db.Close()

	rows, err := db.Query(`
		SELECT c.id, c.symbol, e.id AS exchange_id, c.is_enabled
		FROM cryptos c
		JOIN exchanges_cryptos ec ON c.id = ec.crypto_id
		JOIN exchanges e ON ec.exchange_id = e.id
		WHERE LOWER(e.name) LIKE '%binance%';
	`)
	if err != nil {
		return nil, fmt.Errorf("erro ao buscar criptos: %w", err)
	}
	defer rows.Close()

	var cryptos []EnabledCrypto
	for rows.Next() {
		var crypto EnabledCrypto
		if err := rows.Scan(&crypto.ID, &crypto.Symbol, &crypto.ExchangeID, &crypto.IsEnabled); err != nil {
			return nil, fmt.Errorf("erro ao ler linha: %w", err)
		}
		cryptos = append(cryptos, crypto)
	}

	return cryptos, nil
}

// Salvar progresso em arquivo JSON
func saveProgressData(lastProcessedDate, startedDate *time.Time) error {
	prrogressFile := os.Getenv("DATA_DIR") + "/progress.json"

	// Garantir que o diretório data existe
	if err := os.MkdirAll(filepath.Dir(prrogressFile), 0755); err != nil {
		return fmt.Errorf("erro ao criar diretório para arquivo de progresso: %w", err)
	}

	var data Progress
	// Carregar dados antigos, se existirem
	if _, err := os.Stat(prrogressFile); err == nil {
		file, err := os.ReadFile(prrogressFile)
		if err == nil {
			json.Unmarshal(file, &data)
		}
	}

	// Atualizar dados
	if lastProcessedDate != nil {
		data.LastProcessedDate = lastProcessedDate.Format("2006-01-02")
	}
	if startedDate != nil {
		data.StartedDate = startedDate.Format("2006-01-02")
	}

	// Salvar dados
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("erro ao serializar dados de progresso: %w", err)
	}

	if err := os.WriteFile(prrogressFile, jsonData, 0644); err != nil {
		return fmt.Errorf("erro ao salvar arquivo de progresso: %w", err)
	}

	log.Printf("📌 Progresso salvo: %+v", data)
	return nil
}

// Carregar a última data processada
func loadLastProcessedDate() time.Time {
	prrogressFile := os.Getenv("DATA_DIR") + "/progress.json"

	if _, err := os.Stat(prrogressFile); err == nil {
		file, err := os.ReadFile(prrogressFile)
		if err == nil {
			var data Progress
			log.Printf("📂 Lendo arquivo de progresso: %s", prrogressFile)
			log.Printf("📂 Config encontrada: %s", data)
			if err := json.Unmarshal(file, &data); err == nil && data.LastProcessedDate != "" {
				if date, err := time.Parse("2006-01-02", data.LastProcessedDate); err == nil {
					log.Printf("📅 Última data processada encontrada: %s", date.Format("2006-01-02"))
					return date
				}
			}
		}
	}

	// Se não houver arquivo de progresso ou ocorrer erro, retorne a data atual menos um dia
	log.Println("📅 Nenhuma data processada encontrada, usando data atual menos um dia.")
	return time.Now().AddDate(0, 0, -1)
}

// Carregar a data de início do download
func loadStartedDate() time.Time {
	prrogressFile := os.Getenv("DATA_DIR") + "/progress.json"

	if _, err := os.Stat(prrogressFile); err == nil {
		file, err := os.ReadFile(prrogressFile)
		if err == nil {
			var data Progress
			if err := json.Unmarshal(file, &data); err == nil && data.StartedDate != "" {
				if date, err := time.Parse("2006-01-02", data.StartedDate); err == nil {
					return date
				}
			}
		}
	}

	// Se não houver arquivo de progresso ou ocorrer erro, retorne a data atual
	return time.Now()
}

// Download e extração de arquivos Klines da Binance
func downloadAndExtractKlines(pairs []string, interval string, daysToProcess int, minDate, maxDate string, saveDir string) error {
	// Definir maxDate se não fornecido
	if maxDate == "" {
		maxDate = time.Now().Format("2006-01-02")
	}

	// Carregar a data atual a partir do maxDate
	currentDate, err := time.Parse("2006-01-02", maxDate)
	if err != nil {
		return fmt.Errorf("formato de data inválido: %w", err)
	}

	// Converter a data mínima
	minDateTime, err := time.Parse("2006-01-02", minDate)
	if err != nil {
		return fmt.Errorf("formato de data mínima inválido: %w", err)
	}

	// Salvar a data de início do download
	if err := saveProgressData(nil, &currentDate); err != nil {
		log.Printf("Erro ao salvar data de início: %v", err)
	}

	// Contador de dias processados
	daysProcessed := 0

	// Processar enquanto não atingir o limite de dias ou a data mínima
	for (daysToProcess == 0 || daysProcessed < daysToProcess) && !currentDate.Before(minDateTime) {
		year := currentDate.Year()
		month := currentDate.Month()
		day := currentDate.Day()

		stopGoroutines := false
		totalPairs := len(pairs)

		if stopGoroutines {
			for _, symbol := range pairs {
				downloadAndExtractKlineForSymbol(totalPairs, symbol, interval, year, month, day, saveDir, &stopGoroutines, nil)
			}
		} else {
			var wg sync.WaitGroup
			var mu sync.Mutex

			maxGoroutines := runtime.NumCPU() * 2
			sem := make(chan struct{}, maxGoroutines)

			for _, symbol := range pairs {
				wg.Add(1)
				sem <- struct{}{} // bloquear aqui se já tiver maxGoroutines em execução
				go func(symbol string) {
					defer wg.Done()
					defer func() { <-sem }()
					downloadAndExtractKlineForSymbol(totalPairs, symbol, interval, year, month, day, saveDir, &stopGoroutines, &mu)
				}(symbol)
			}
			wg.Wait()
		}

		// Salvar o progresso atual antes de ir para o próximo dia
		if err := saveProgressData(&currentDate, nil); err != nil {
			log.Printf("Erro ao salvar progresso: %v", err)
		}

		// Ir para o dia anterior
		currentDate = currentDate.AddDate(0, 0, -1)
		daysProcessed++

		// Log de progresso
		log.Printf("📅 Processado dia: %s (%d dias)", currentDate.Format("2006-01-02"), daysProcessed)
	}

	return nil
}

func downloadAndExtractKlineForSymbol(totalPairs int, symbol, interval string, year int, month time.Month, day int, saveDir string, stopGorotines *bool, mu *sync.Mutex) {
	baseURL := "https://data.binance.vision/data/spot/daily/klines"
	zipDir := filepath.Join(saveDir+"/data.binance.vision/data/spot/daily/klines", symbol, interval, "zip")
	csvDir := filepath.Join(saveDir+"/data.binance.vision/data/spot/daily/klines", symbol, interval, "csv")

	// Criar diretórios se não existirem
	if err := os.MkdirAll(zipDir, 0755); err != nil {
		log.Printf("Erro ao criar diretório zip: %v", err)
		return
	}
	if err := os.MkdirAll(csvDir, 0755); err != nil {
		log.Printf("Erro ao criar diretório csv: %v", err)
		return
	}

	monthStr := fmt.Sprintf("%02d", month)
	dayStr := fmt.Sprintf("%02d", day)
	fileName := fmt.Sprintf("%s-%s-%d-%s-%s.zip", symbol, interval, year, monthStr, dayStr)
	url := fmt.Sprintf("%s/%s/%s/%s", baseURL, symbol, interval, fileName)
	zipPath := filepath.Join(zipDir, fileName)
	csvFilePath := filepath.Join(csvDir, fileName[:len(fileName)-4]+".csv")

	// Verificar se o arquivo CSV já existe
	if _, err := os.Stat(csvFilePath); err == nil {
		*stopGorotines = false
		return
	}

	if isOfflineLink(url) {
		*stopGorotines = false
		return
	}

	*stopGorotines = true
	log.Printf("⬇️ Baixando: %s", url)

	// Fazer o download do arquivo
	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	if mu != nil {
		mu.Lock()
	}
	resp, err := client.Get(url)
	time.Sleep(1 * time.Second) // Aguardar um segundo antes de continuar
	if mu != nil {
		mu.Unlock()
	}
	if err != nil {
		log.Printf("⚠️ Erro ao baixar %s: %v", fileName, err)
		insertOfflineLink(url)
		return
	}

	if resp.StatusCode != http.StatusOK {
		log.Printf("❌ Arquivo não encontrado: %s (status %d)", fileName, resp.StatusCode)
		resp.Body.Close()
		insertOfflineLink(url)
		return
	}

	// Criar arquivo zip
	zipFile, err := os.Create(zipPath)
	if err != nil {
		log.Printf("❌ Erro ao criar arquivo zip: %v", err)
		resp.Body.Close()
		return
	}

	// Copiar conteúdo do response para o arquivo
	_, err = io.Copy(zipFile, resp.Body)
	resp.Body.Close()
	zipFile.Close()

	if err != nil {
		log.Printf("❌ Erro ao salvar arquivo zip: %v", err)
		return
	}

	// Extrair o ZIP
	if err := extractZip(zipPath, csvDir); err != nil {
		log.Printf("❌ Erro ao extrair %s: %v", zipPath, err)
		return
	}

	log.Printf("📦 Extraído para: %s", csvDir)

	// Remover o arquivo ZIP após a extração
	if err := os.Remove(zipPath); err != nil {
		log.Printf("⚠️ Erro ao remover arquivo zip: %v", err)
	}
}

// Função para extrair arquivos zip
func extractZip(zipPath, destDir string) error {
	r, err := zip.OpenReader(zipPath)
	if err != nil {
		return fmt.Errorf("erro ao abrir zip: %w", err)
	}
	defer r.Close()

	for _, f := range r.File {
		rc, err := f.Open()
		if err != nil {
			return fmt.Errorf("erro ao abrir arquivo no zip: %w", err)
		}

		path := filepath.Join(destDir, f.Name)

		if f.FileInfo().IsDir() {
			os.MkdirAll(path, 0755)
		} else {
			os.MkdirAll(filepath.Dir(path), 0755)
			outFile, err := os.Create(path)
			if err != nil {
				rc.Close()
				return fmt.Errorf("erro ao criar arquivo de saída: %w", err)
			}

			_, err = io.Copy(outFile, rc)
			outFile.Close()
			if err != nil {
				rc.Close()
				return fmt.Errorf("erro ao copiar conteúdo: %w", err)
			}
		}
		rc.Close()
	}

	return nil
}

func isOfflineLink(link string) bool {
	offlineFile := os.Getenv("DATA_DIR") + "/offline_links.txt"
	// Verifica se o diretório existe, se não, cria
	if err := os.MkdirAll(filepath.Dir(offlineFile), 0755); err != nil {
		log.Printf("Erro ao criar diretório para offline_links.txt: %v", err)
		return false
	}
	// Tenta abrir o arquivo, se não existir, cria
	if _, err := os.Stat(offlineFile); os.IsNotExist(err) {
		file, err := os.Create(offlineFile)
		if err != nil {
			log.Printf("Erro ao criar offline_links.txt: %v", err)
			return false
		}
		file.Close()
	}

	// Se o arquivo existir, verifica se alguma linha contém o link
	content, err := os.ReadFile(offlineFile)
	if err != nil {
		log.Printf("Erro ao ler offline_links.txt: %v", err)
		return false
	}
	lines := string(content)
	if lines != "" {
		for _, line := range splitLines(lines) {
			if line != "" && contains(line, link) {
				return true
			}
		}
	}
	return false
}

// contains verifica se substr está contido em s
func contains(s, substr string) bool {
	return len(substr) > 0 && len(s) >= len(substr) && (s == substr || (len(s) > len(substr) && (len(s) > 0 && len(substr) > 0 && (len(s) >= len(substr) && (func() bool {
		for i := 0; i <= len(s)-len(substr); i++ {
			if s[i:i+len(substr)] == substr {
				return true
			}
		}
		return false
	}())))))
}

// splitLines divide uma string em linhas, suportando \n e \r\n
func splitLines(s string) []string {
	var lines []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			line := s[start:i]
			if len(line) > 0 && line[len(line)-1] == '\r' {
				line = line[:len(line)-1]
			}
			lines = append(lines, line)
			start = i + 1
		}
	}
	if start < len(s) {
		lines = append(lines, s[start:])
	}
	return lines
}

func insertOfflineLink(link string) {
	offlineFile := os.Getenv("DATA_DIR") + "/offline_links.txt"

	// Verifica se o diretório existe, se não, cria
	if err := os.MkdirAll(filepath.Dir(offlineFile), 0755); err != nil {
		log.Printf("Erro ao criar diretório para offline_links.txt: %v", err)
		return
	}

	// Abre o arquivo offline_links.txt para adicionar o link
	file, err := os.OpenFile(offlineFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Erro ao abrir offline_links.txt: %v", err)
		return
	}
	defer file.Close()

	if _, err := file.WriteString(link + "\n"); err != nil {
		log.Printf("Erro ao escrever no arquivo offline_links.txt: %v", err)
	}
}
