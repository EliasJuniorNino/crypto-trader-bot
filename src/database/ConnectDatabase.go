package database

import (
	"database/sql"
	"log"
	"os"
)

func ConnectDatabase() (*sql.DB, error) {
	db_url := os.Getenv("DATA_DIR") + "/database.db"
	db, err := sql.Open("sqlite", db_url)
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %s, %v", db_url, err)
	}
	return db, err
}
