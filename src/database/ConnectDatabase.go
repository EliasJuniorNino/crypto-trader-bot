package database

import (
	"database/sql"
	"log"
)

func ConnectDatabase() (*sql.DB, error) {
	db, err := sql.Open("sqlite3", "database/database.db")
	if err != nil {
		log.Fatalf("Erro ao abrir o banco de dados: %v", err)
	}
	return db, err
}
