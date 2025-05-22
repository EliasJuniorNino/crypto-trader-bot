package scripts

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"time"

	_ "github.com/joho/godotenv/autoload"
	_ "github.com/mattn/go-sqlite3"
)

// Configurações globais
const (
	_SQLiteDBPath = "database/database.db"
)

// Estrutura para criptomoedas habilitadas
type _Crypto struct {
	ID         int
	Symbol     string
	ExchangeID int
	IsEnabled  int
}

// Conectar ao banco de dados SQLite
func _connectDB() (*sql.DB, error) {
	db, err := sql.Open("sqlite3", _SQLiteDBPath)
	if err != nil {
		return nil, fmt.Errorf("erro ao conectar ao banco SQLite: %w", err)
	}
	return db, nil
}

// Obter criptomoedas habilitadas
func _getEnabledCryptos() ([]_Crypto, error) {
	db, err := _connectDB()
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

	var cryptos []_Crypto
	for rows.Next() {
		var crypto _Crypto
		if err := rows.Scan(&crypto.ID, &crypto.Symbol, &crypto.ExchangeID, &crypto.IsEnabled); err != nil {
			return nil, fmt.Errorf("erro ao ler linha: %w", err)
		}
		cryptos = append(cryptos, crypto)
	}

	return cryptos, nil
}

// Desativar criptomoeda no banco de dados
func _disableCrypto(cryptoID int) error {
	db, err := _connectDB()
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec("UPDATE cryptos SET is_enabled = 0 WHERE id = ?", cryptoID)
	if err != nil {
		return fmt.Errorf("erro ao desativar crypto ID %d: %w", cryptoID, err)
	}

	log.Printf("🚫 Criptomoeda ID %d desativada no banco de dados", cryptoID)
	return nil
}

// Verificar se uma criptomoeda está disponível na Binance em uma data específica
func _checkCryptoAvailability(symbol, interval, date string) bool {
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
	fileName := fmt.Sprintf("%s-%s-%d-%s-%s.zip", symbol, interval, year, monthStr, dayStr)
	url := fmt.Sprintf("%s/%s/%s/%s", baseURL, symbol, interval, fileName)

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
func DisableCryptos(minDate, maxDate string) {
	// Configurar logging
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("INFO: ")

	log.Printf("🚀 Iniciando verificação de disponibilidade de criptos")
	log.Printf("📅 Período: %s até %s", minDate, maxDate)

	// Obter criptos habilitadas
	cryptos, err := _getEnabledCryptos()
	if err != nil {
		log.Printf("❌ Erro ao obter criptos: %v", err)
		return
	}

	if len(cryptos) == 0 {
		log.Println("⚠️ Nenhuma criptomoeda habilitada encontrada.")
		return
	}

	log.Printf("📊 Total de criptomoedas a verificar: %d", len(cryptos))

	// Verificar cada crypto nas duas datas
	for index, crypto := range cryptos {
		symbol := fmt.Sprintf("%sUSDT", crypto.Symbol)
		log.Printf("👉 (%d/%d) Verificando %s (ID: %d)", index+1, len(cryptos), symbol, crypto.ID)

		// Verificar disponibilidade na data mínima
		availableMinDate := _checkCryptoAvailability(symbol, "1m", minDate)

		// Verificar disponibilidade na data máxima
		availableMaxDate := _checkCryptoAvailability(symbol, "1m", maxDate)

		// Se retornou 404 em ambas as datas, desativar a crypto
		if !availableMinDate || !availableMaxDate {
			log.Printf("🚫 %s indisponível em uma das datas. Desativando...", symbol)
			if err := _disableCrypto(crypto.ID); err != nil {
				log.Printf("❌ Erro ao desativar %s: %v", symbol, err)
			}
		} else {
			log.Printf("✅ %s está disponível em pelo menos uma das datas", symbol)
		}

		// Aguardar um pouco entre as requisições para não sobrecarregar a API
		time.Sleep(500 * time.Millisecond)
	}

	log.Printf("✨ Verificação concluída!")
}
