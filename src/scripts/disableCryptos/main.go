package disableCryptos

import (
	"app/src/database"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	_ "github.com/joho/godotenv/autoload"
	_ "github.com/mattn/go-sqlite3"
)

// Estrutura para criptomoedas habilitadas
type crypto struct {
	ID         int
	Symbol     string
	ExchangeID int
	IsEnabled  int
}

// Obter criptomoedas habilitadas
func getCryptos() ([]crypto, error) {
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

	var cryptos []crypto
	for rows.Next() {
		var crypto crypto
		if err := rows.Scan(&crypto.ID, &crypto.Symbol, &crypto.ExchangeID, &crypto.IsEnabled); err != nil {
			return nil, fmt.Errorf("erro ao ler linha: %w", err)
		}
		cryptos = append(cryptos, crypto)
	}

	return cryptos, nil
}

// Desativar criptomoeda no banco de dados
func disableCrypto(crypto string) error {
	db, err := database.ConnectDatabase()
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec("UPDATE cryptos SET is_enabled = 0 WHERE symbol = ?", crypto)
	if err != nil {
		return fmt.Errorf("erro ao desativar crypto ID %s: %w", crypto, err)
	}

	log.Printf("🚫 Criptomoeda ID %s desativada no banco de dados", crypto)
	return nil
}

func enableCrypto(crypto string) error {
	db, err := database.ConnectDatabase()
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec("UPDATE cryptos SET is_enabled = 1 WHERE symbol = ?", crypto)
	if err != nil {
		return fmt.Errorf("erro ao ativar crypto %s: %w", crypto, err)
	}

	log.Printf("✅ Criptomoeda %s ativada no banco de dados", crypto)
	return nil
}

// Verificar se uma criptomoeda está disponível na Binance em uma data específica
func checkCryptoAvailability(symbol, interval, date string) bool {
	dateTime, err := time.Parse("2006-01-02", date)
	if err != nil {
		log.Printf("❌ Formato de data inválido: %v", err)
		return false
	}

	year := dateTime.Year()
	month := dateTime.Month()
	day := dateTime.Day()

	baseURL := "https://data.binance.vision/data/spot/daily/klines"
	monthStr := fmt.Sprintf("%02d", month)
	dayStr := fmt.Sprintf("%02d", day)
	fileName := fmt.Sprintf("%s-%s-%d-%s-%s", symbol, interval, year, monthStr, dayStr)
	url := fmt.Sprintf("%s/%s/%s/%s.zip", baseURL, symbol, interval, fileName)

	csvDir := filepath.Join("data", "binance_data", symbol, interval, "csv")
	csvFilePath := filepath.Join(csvDir, fileName+".csv")

	// Verificar se o arquivo CSV já existe
	if _, err := os.Stat(csvFilePath); err == nil {
		return true
	} else {
		log.Printf("⚠️ Arquivo não encontrado %s", csvFilePath)
	}

	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	resp, err := client.Get(url)
	if err != nil {
		log.Printf("⚠️ Erro ao verificar %s: %v", symbol, err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		log.Printf("❌ 404 - Arquivo não encontrado: %s", fileName)
		return false
	}

	if resp.StatusCode == http.StatusOK {
		log.Printf("✅ Disponível: %s", fileName)
		return true
	}

	log.Printf("⚠️ Status %d para %s", resp.StatusCode, fileName)
	return false
}

// Função principal para desativar criptos indisponíveis
func Main(minDate, maxDate string) {
	// Configurar logging
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("INFO: ")

	log.Printf("🚀 Iniciando verificação de disponibilidade de criptos")
	log.Printf("📅 Período: %s até %s", minDate, maxDate)

	// Obter criptos habilitadas
	cryptos, err := getCryptos()
	if err != nil {
		log.Printf("❌ Erro ao obter criptos: %v", err)
		return
	}

	if len(cryptos) == 0 {
		log.Println("⚠️ Nenhuma criptomoeda habilitada encontrada.")
		return
	}

	log.Printf("📊 Total de criptomoedas a verificar: %d", len(cryptos))

	disabledCryptos := make(map[string]bool)
	// Verificar cada crypto nas duas datas
	for index, crypto := range cryptos {
		symbol := fmt.Sprintf("%sUSDT", crypto.Symbol)

		if disabledCryptos[symbol] {
			log.Printf("👉 (%d/%d) Crypto já desativada, ignorando %s (ID: %d)", index+1, len(cryptos), symbol, crypto.ID)
			continue
		}

		log.Printf("👉 (%d/%d) Verificando %s (ID: %d)", index+1, len(cryptos), symbol, crypto.ID)

		// Verificar disponibilidade na data mínima
		availableMinDate := checkCryptoAvailability(symbol, "1m", minDate)

		// Verificar disponibilidade na data máxima
		availableMaxDate := checkCryptoAvailability(symbol, "1m", maxDate)

		// Se retornou 404 em ambas as datas, desativar a crypto
		if !availableMinDate || !availableMaxDate {
			log.Printf("🚫 %s indisponível em uma das datas. Desativando...", symbol)
			if err := disableCrypto(crypto.Symbol); err != nil {
				log.Printf("❌ Erro ao desativar %s: %v", symbol, err)
			}
			disabledCryptos[symbol] = true
			log.Printf("☐ %s desativada", symbol)
			continue
		} else {
			log.Printf("✅ %s está disponível em pelo menos uma das datas", symbol)
		}

		initialDate, err := time.Parse("2006-01-02", minDate)
		if err != nil {
			log.Printf("❌ Erro ao ler data %s: %v", minDate, err)
			return
		}

		endDate, err := time.Parse("2006-01-02", maxDate)
		if err != nil {
			log.Printf("❌ Erro ao ler data %s: %v", maxDate, err)
			return
		}

		for i := initialDate; i.Before(time.Now().UTC()) && (i.Before(endDate) || i.Equal(endDate)); i = i.Add(24 * time.Hour) {
			currentDateStr := i.Format("2006-01-02")
			isAvailable := checkCryptoAvailability(symbol, "1m", currentDateStr)
			if !isAvailable {
				if err := disableCrypto(crypto.Symbol); err != nil {
					log.Printf("❌ Erro ao desativar %s: %v", symbol, err)
				}
				disabledCryptos[symbol] = true
				log.Printf("☐ %s desativada", symbol)
				break
			}
		}

		if !disabledCryptos[symbol] {
			if err := enableCrypto(crypto.Symbol); err != nil {
				log.Printf("❌ Erro ao ativar %s: %v", symbol, err)
			} else {
				log.Printf("✅ %s ativada", symbol)
			}
		}

		// Aguardar um pouco entre as requisições para não sobrecarregar a API
		time.Sleep(500 * time.Millisecond)
	}

	log.Printf("✨ Verificação concluída!")
}
