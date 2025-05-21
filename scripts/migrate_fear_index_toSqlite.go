package scripts

import (
	"database/sql"
	"fmt"
	"os"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
	_ "github.com/mattn/go-sqlite3"
)

type FearIndex struct {
	ID     int64
	Source string
	Target sql.NullString
	Date   time.Time
	Value  float64
}

func MigrateFearIndex() {
	fmt.Println("=== Migrador de MySQL para SQLite - Tabela fear_index ===")

	// Carregar variáveis de ambiente do arquivo .env
	err := godotenv.Load()
	if err != nil {
		fmt.Println("Aviso: não foi possível carregar o arquivo .env (continuando com variáveis de ambiente existentes).")
	}

	// Caminho do banco de dados SQLite
	sqlitePath := "database/database.db"
	fmt.Printf("Caminho do banco de dados SQLite: %s\n", sqlitePath)

	// Verificar se o arquivo SQLite existe
	if _, err := os.Stat(sqlitePath); err != nil {
		fmt.Printf("O arquivo %s não existe.\n", sqlitePath)
		return
	}

	// Conectar ao MySQL
	fmt.Println("Conectando ao MySQL...")
	mysqlDSN := fmt.Sprintf(
		"%s:%s@tcp(%s:%s)/%s",
		os.Getenv("DATABASE_USER"),
		os.Getenv("DATABASE_PASSWORD"),
		os.Getenv("DATABASE_HOST"),
		os.Getenv("DATABASE_PORT"),
		os.Getenv("DATABASE_DBNAME"),
	)
	mysqlDB, err := sql.Open("mysql", mysqlDSN)
	if err != nil {
		fmt.Printf("Erro ao conectar ao MySQL: %v\n", err)
		return
	}
	defer mysqlDB.Close()

	// Conectar ao SQLite
	fmt.Printf("Conectando ao SQLite em %s...\n", sqlitePath)
	sqliteDB, err := sql.Open("sqlite3", sqlitePath)
	if err != nil {
		fmt.Printf("Erro ao conectar ao SQLite: %v\n", err)
		return
	}
	defer sqliteDB.Close()

	// Obter dados do MySQL
	fmt.Println("Obtendo dados da tabela fear_index...")
	rows, err := mysqlDB.Query("SELECT id, source, target, date, value FROM fear_index")
	if err != nil {
		fmt.Printf("Erro ao consultar dados no MySQL: %v\n", err)
		return
	}
	defer rows.Close()

	var fearIndices []FearIndex
	for rows.Next() {
		var fi FearIndex
		var dateBytes []byte
		err := rows.Scan(&fi.ID, &fi.Source, &fi.Target, &dateBytes, &fi.Value)
		if err != nil {
			fmt.Printf("Erro ao ler registro do MySQL: %v\n", err)
			continue
		}
		dateStr := string(dateBytes)
		fi.Date, err = time.Parse("2006-01-02 15:04:05", dateStr)
		if err != nil {
			fmt.Printf("Erro ao converter data: %v\n", err)
			continue
		}
		fearIndices = append(fearIndices, fi)
	}
	fmt.Printf("Encontrados %d registros para migração.\n", len(fearIndices))

	// Drop da tabela (se existir)
	fmt.Println("Removendo tabela fear_index no SQLite (se existir)...")
	_, err = sqliteDB.Exec("DROP TABLE IF EXISTS fear_index;")
	if err != nil {
		fmt.Printf("Erro ao remover tabela no SQLite: %v\n", err)
		return
	}

	// Criar tabela
	fmt.Println("Criando tabela no SQLite...")
	_, err = sqliteDB.Exec(`
		CREATE TABLE IF NOT EXISTS fear_index (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			source TEXT NOT NULL,
			target TEXT,
			date DATETIME NOT NULL,
			value REAL NOT NULL,
			UNIQUE (source, target, date)
		)
	`)
	if err != nil {
		fmt.Printf("Erro ao criar tabela no SQLite: %v\n", err)
		return
	}

	// Iniciar transação
	fmt.Println("Migrando dados...")
	tx, err := sqliteDB.Begin()
	if err != nil {
		fmt.Printf("Erro ao iniciar transação SQLite: %v\n", err)
		return
	}

	stmt, err := tx.Prepare("INSERT OR IGNORE INTO fear_index (id, source, target, date, value) VALUES (?, ?, ?, ?, ?)")
	if err != nil {
		fmt.Printf("Erro ao preparar statement: %v\n", err)
		tx.Rollback()
		return
	}
	defer stmt.Close()

	successCount := 0
	for _, fi := range fearIndices {
		_, err := stmt.Exec(fi.ID, fi.Source, fi.Target, fi.Date.Format("2006-01-02 15:04:05"), fi.Value)
		if err != nil {
			fmt.Printf("Erro ao inserir registro ID=%d: %v\n", fi.ID, err)
			continue
		}
		successCount++
		if successCount%100 == 0 {
			fmt.Printf("Progresso: %d/%d registros migrados\n", successCount, len(fearIndices))
		}
	}

	// Confirmar transação
	err = tx.Commit()
	if err != nil {
		fmt.Printf("Erro ao confirmar transação: %v\n", err)
		tx.Rollback()
		return
	}

	// Verificar contagem final
	var sqliteCount int
	err = sqliteDB.QueryRow("SELECT COUNT(*) FROM fear_index").Scan(&sqliteCount)
	if err != nil {
		fmt.Printf("Erro ao contar registros no SQLite: %v\n", err)
	} else {
		fmt.Printf("Total de registros no SQLite após migração: %d\n", sqliteCount)
	}

	fmt.Printf("Migração concluída! %d de %d registros migrados com sucesso.\n", successCount, len(fearIndices))
	fmt.Println("=== Fim do processo de migração ===")
}
