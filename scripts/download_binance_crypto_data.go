package scripts

import (
	"archive/zip"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	_ "github.com/joho/godotenv/autoload"
	_ "github.com/mattn/go-sqlite3"
)

// Configurações globais
const (
	SQLiteDBPath = "database/database.db"
	ProgressFile = "data/progress.json"
)

// Estrutura para armazenar progresso
type Progress struct {
	LastProcessedDate string `json:"last_processed_date,omitempty"`
	StartedDate       string `json:"started_date,omitempty"`
}

// Estrutura para criptomoedas habilitadas
type Crypto struct {
	ID         int
	Symbol     string
	ExchangeID int
	IsEnabled  int
}

// Conectar ao banco de dados SQLite
func connectDB() (*sql.DB, error) {
	db, err := sql.Open("sqlite3", SQLiteDBPath)
	if err != nil {
		return nil, fmt.Errorf("erro ao conectar ao banco SQLite: %w", err)
	}
	log.Println("Conexão com o banco SQLite estabelecida.")
	return db, nil
}

// Obter criptomoedas habilitadas
func getEnabledCryptos() ([]Crypto, error) {
	db, err := connectDB()
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

	var cryptos []Crypto
	for rows.Next() {
		var crypto Crypto
		if err := rows.Scan(&crypto.ID, &crypto.Symbol, &crypto.ExchangeID, &crypto.IsEnabled); err != nil {
			return nil, fmt.Errorf("erro ao ler linha: %w", err)
		}
		cryptos = append(cryptos, crypto)
	}

	return cryptos, nil
}

// Salvar progresso em arquivo JSON
func saveProgressData(lastProcessedDate, startedDate *time.Time) error {
	// Garantir que o diretório data existe
	if err := os.MkdirAll(filepath.Dir(ProgressFile), 0755); err != nil {
		return fmt.Errorf("erro ao criar diretório para arquivo de progresso: %w", err)
	}

	var data Progress
	// Carregar dados antigos, se existirem
	if _, err := os.Stat(ProgressFile); err == nil {
		file, err := os.ReadFile(ProgressFile)
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

	if err := os.WriteFile(ProgressFile, jsonData, 0644); err != nil {
		return fmt.Errorf("erro ao salvar arquivo de progresso: %w", err)
	}

	log.Printf("📌 Progresso salvo: %+v", data)
	return nil
}

// Carregar a última data processada
func loadLastProcessedDate() time.Time {
	if _, err := os.Stat(ProgressFile); err == nil {
		file, err := os.ReadFile(ProgressFile)
		if err == nil {
			var data Progress
			if err := json.Unmarshal(file, &data); err == nil && data.LastProcessedDate != "" {
				if date, err := time.Parse("2006-01-02", data.LastProcessedDate); err == nil {
					return date
				}
			}
		}
	}

	// Se não houver arquivo de progresso ou ocorrer erro, retorne a data atual menos um dia
	return time.Now().AddDate(0, 0, -1)
}

// Carregar a data de início do download
func loadStartedDate() time.Time {
	if _, err := os.Stat(ProgressFile); err == nil {
		file, err := os.ReadFile(ProgressFile)
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

		for index, symbol := range pairs {
			fmt.Println()
			log.Printf("👉 %s(%d/%d)", symbol, index+1, len(pairs))

			baseURL := "https://data.binance.vision/data/spot/daily/klines"
			zipDir := filepath.Join(saveDir, symbol, interval, "zip")
			csvDir := filepath.Join(saveDir, symbol, interval, "csv")

			// Criar diretórios se não existirem
			if err := os.MkdirAll(zipDir, 0755); err != nil {
				log.Printf("Erro ao criar diretório zip: %v", err)
				continue
			}
			if err := os.MkdirAll(csvDir, 0755); err != nil {
				log.Printf("Erro ao criar diretório csv: %v", err)
				continue
			}

			monthStr := fmt.Sprintf("%02d", month)
			dayStr := fmt.Sprintf("%02d", day)
			fileName := fmt.Sprintf("%s-%s-%d-%s-%s.zip", symbol, interval, year, monthStr, dayStr)
			url := fmt.Sprintf("%s/%s/%s/%s", baseURL, symbol, interval, fileName)
			zipPath := filepath.Join(zipDir, fileName)
			csvFilePath := filepath.Join(csvDir, fileName[:len(fileName)-4]+".csv")

			// Verificar se o arquivo CSV já existe
			if _, err := os.Stat(csvFilePath); err == nil {
				log.Printf("✅ Já extraído: %s", fileName)
				continue
			}

			log.Printf("⬇️ Baixando: %s", url)

			// Fazer o download do arquivo
			client := &http.Client{
				Timeout: 10 * time.Second,
			}

			resp, err := client.Get(url)
			if err != nil {
				log.Printf("⚠️ Erro ao baixar %s: %v", fileName, err)
				continue
			}

			if resp.StatusCode != http.StatusOK {
				log.Printf("❌ Arquivo não encontrado: %s (status %d)", fileName, resp.StatusCode)
				resp.Body.Close()
				continue
			}

			// Criar arquivo zip
			zipFile, err := os.Create(zipPath)
			if err != nil {
				log.Printf("❌ Erro ao criar arquivo zip: %v", err)
				resp.Body.Close()
				continue
			}

			// Copiar conteúdo do response para o arquivo
			_, err = io.Copy(zipFile, resp.Body)
			resp.Body.Close()
			zipFile.Close()

			if err != nil {
				log.Printf("❌ Erro ao salvar arquivo zip: %v", err)
				continue
			}

			log.Printf("✔️ Salvo: %s", zipPath)

			// Extrair o ZIP
			if err := extractZip(zipPath, csvDir); err != nil {
				log.Printf("❌ Erro ao extrair %s: %v", zipPath, err)
				continue
			}

			log.Printf("📦 Extraído para: %s", csvDir)

			// Aguardar um segundo antes de continuar
			time.Sleep(1 * time.Second)
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

func download_bynance_crypto_data() {
	// Configurar logging
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("INFO: ")

	// Obter criptos habilitadas
	cryptos, err := getEnabledCryptos()
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
				"data/binance_data",
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
			"data/binance_data",
		)
		if err != nil {
			log.Printf("Erro ao baixar dados históricos: %v", err)
		}
	} else {
		log.Println("Nenhuma criptomoeda habilitada encontrada.")
	}
}
