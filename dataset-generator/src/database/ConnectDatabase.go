package database

import (
	"database/sql"
	"log"
	"os"
)

func ConnectDatabase() (*sql.DB, error) {
	db, err := sql.Open("sqlite3", os.Getenv("DATA_DIR")+"/database.db")
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	return db, err
}
