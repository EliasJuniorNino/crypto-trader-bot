package getFearIndex

import (
	"app/src/constants"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/mattn/go-sqlite3"
)

type apiResponse struct {
	Data []fearData `json:"data"`
}

type fearData struct {
	Timestamp string  `json:"timestamp"`
	Value     float64 `json:"value"`
}

func GetFearCoinmarketcap(isSearchForAllFlg bool) {
	fmt.Println("=== Importador de Fear & Greed Index ===")

	err := godotenv.Load()
	if err != nil {
		fmt.Println("Aviso: não foi possível carregar .env, usando variáveis do ambiente.")
	}

	apiKey := os.Getenv("COINMARKETCAP_API_KEY")
	if apiKey == "" {
		fmt.Println("Erro: variável COINMARKETCAP_API_KEY não definida.")
		return
	}

	dbPath := "database/database.db"
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		fmt.Printf("Erro ao conectar ao SQLite: %v\n", err)
		return
	}
	defer db.Close()

	err = createTableIfNotExists(db)
	if err != nil {
		fmt.Printf("Erro ao garantir tabela: %v\n", err)
		return
	}

	allInserted := 0
	limit := 50
	start := 1
	for {
		data, err := fetchFearData(apiKey, limit, start)
		if err != nil {
			fmt.Printf("Erro ao buscar dados da API: %v\n", err)
			return
		}

		inserted := 0
		for _, item := range data {
			timestamp, err := strconv.ParseInt(item.Timestamp, 10, 64)
			if err != nil {
				fmt.Printf("Erro ao converter: %v\n", err)
				return
			}

			date := time.Unix(timestamp, 0).Format("2006-01-02 15:04:05")

			exists, err := recordExists(db, date)
			if err != nil {
				fmt.Printf("Erro ao verificar duplicidade: %v\n", err)
				continue
			}
			if exists {
				fmt.Printf("Registro %s já existe. Ignorando.\n", date)
				continue
			}

			err = insertRecord(db, "CoinMarketCap", nil, date, item.Value)
			if err != nil {
				fmt.Printf("Erro ao inserir registro: %v\n", err)
				continue
			}
			inserted++
		}
		allInserted += inserted
		if len(data) == 0 || !isSearchForAllFlg {
			break
		}
		start += limit
	}
	fmt.Printf("%d registros inseridos com sucesso!\n", allInserted)
}

func fetchFearData(apiKey string, limit int, start int) ([]fearData, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	req, err := http.NewRequest("GET", constants.COINMARKETCAP_FEAR_HISTORICAL_API, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("X-CMC_PRO_API_KEY", apiKey)

	q := req.URL.Query()
	q.Add("limit", fmt.Sprintf("%d", limit))
	q.Add("start", fmt.Sprintf("%d", start))
	req.URL.RawQuery = q.Encode()

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("erro HTTP: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("resposta inválida: %s", string(body))
	}

	var apiResp apiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, fmt.Errorf("erro ao decodificar JSON: %v", err)
	}

	return apiResp.Data, nil
}

func createTableIfNotExists(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS fear_index (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		source TEXT NOT NULL,
		target TEXT,
		date DATETIME NOT NULL,
		value REAL NOT NULL,
		UNIQUE(source, target, date)
	);`
	_, err := db.Exec(query)
	return err
}

func recordExists(db *sql.DB, date string) (bool, error) {
	var exists int
	query := `SELECT 1 FROM fear_index WHERE date = ? AND source = 'CoinMarketCap' LIMIT 1`
	err := db.QueryRow(query, date).Scan(&exists)
	if err == sql.ErrNoRows {
		return false, nil
	}
	return err == nil, err
}

func insertRecord(db *sql.DB, source string, target *string, date string, value float64) error {
	_, err := db.Exec(
		`INSERT INTO fear_index (source, target, date, value) VALUES (?, ?, ?, ?)`,
		source, target, date, value,
	)
	return err
}
