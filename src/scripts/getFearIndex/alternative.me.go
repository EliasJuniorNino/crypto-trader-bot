package getFearIndex

import (
	"app/src/constants"
	"app/src/database"
	"app/src/dto"
	"app/src/models"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/mattn/go-sqlite3"
)

func GetFearAlternativeMe() {
	fmt.Println("=== Importador do índice de medo/ganância - Alternative.me ===")

	err := godotenv.Load()
	if err != nil {
		fmt.Println("Aviso: não foi possível carregar .env, usando variáveis do ambiente.")
	}

	// Conexão com o banco de dados
	db, err := database.ConnectDatabase()
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	defer db.Close()

	err = createTableIfNotExists(db)
	if err != nil {
		fmt.Printf("Erro ao garantir tabela: %v\n", err)
		return
	}

	data, err := fetchAlternativeFearData()
	if err != nil {
		fmt.Printf("Erro ao buscar dados da API: %v\n", err)
		return
	}

	inserted := 0
	for _, item := range data {
		// Convertendo timestamp string para int64
		timestampInt, err := strconv.ParseInt(item.Timestamp, 10, 64)
		if err != nil {
			fmt.Printf("Erro ao converter timestamp: %v\n", err)
			continue
		}
		date := time.Unix(timestampInt, 0).Format("2006-01-02 15:04:05")

		// Convertendo valor para float64
		value, err := strconv.ParseFloat(item.Value, 64)
		if err != nil {
			fmt.Printf("Erro ao converter valor: %v\n", err)
			continue
		}

		exists, err := recordExistsAlternative(db, date)
		if err != nil {
			fmt.Printf("Erro ao verificar duplicidade: %v\n", err)
			continue
		}
		if exists {
			fmt.Printf("Registro %s já existe. Ignorando.\n", date)
			continue
		}

		err = insertRecord(db, "api.alternative.me", nil, date, value)
		if err != nil {
			fmt.Printf("Erro ao inserir registro: %v\n", err)
			continue
		}
		inserted++
	}

	fmt.Printf("%d registros inseridos com sucesso!\n", inserted)
}

func fetchAlternativeFearData() ([]models.AlternativeFearData, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(constants.ALTERNATIVE_ME_API + "/?limit=9999999999999999999")
	if err != nil {
		return nil, fmt.Errorf("erro HTTP: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("resposta inválida: %s", string(body))
	}

	var apiResp dto.AlternativeAPIResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, fmt.Errorf("erro ao decodificar JSON: %v", err)
	}

	return apiResp.Data, nil
}

func recordExistsAlternative(db *sql.DB, date string) (bool, error) {
	var exists int
	query := `SELECT 1 FROM fear_index WHERE date = ? AND source = 'api.alternative.me' LIMIT 1`
	err := db.QueryRow(query, date).Scan(&exists)
	if err == sql.ErrNoRows {
		return false, nil
	}
	return err == nil, err
}
