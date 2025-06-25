package generateModels

import (
	"app/src/database"
	"database/sql"
	"fmt"
	"log"
	"os/exec"
)

func Main() {
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

	for _, coin := range cryptos {
		err := generateModels(coin)
		if err != nil {
			log.Fatalf("Erro ao gerar modelos para a moeda %s: %v", coin, err)
		} else {
			fmt.Printf("Modelos gerados com sucesso para a moeda: %s\n", coin)
		}
	}
}

func generateModels(coin string) error {
	cmd := exec.Command("python", "./model-generator/generate_models_rf_v1.py", "--coin="+coin)
	cmd.Stdout = nil // pode redirecionar se quiser
	cmd.Stderr = nil
	err := cmd.Run()
	if err != nil {
		log.Fatalf("Erro ao executar o script Python: %v", err)
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
