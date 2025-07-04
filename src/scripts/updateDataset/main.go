package updateDataset

import (
	"encoding/csv"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func Main() {
	finalDatasetDir := filepath.Join(os.Getenv("DATASET_DIR"))
	finalDatasetFilePath := filepath.Join(finalDatasetDir, "dataset_full.csv")
	percentFilePath := filepath.Join(finalDatasetDir, "dataset_percent.csv")

	inFile, err := os.Open(finalDatasetFilePath)
	if err != nil {
		log.Fatalf("Erro ao abrir arquivo original: %v", err)
	}

	reader := csv.NewReader(inFile)

	outFile, err := os.Create(percentFilePath)
	if err != nil {
		log.Fatalf("Erro ao criar arquivo temporário: %v", err)
	}

	writer := csv.NewWriter(outFile)
	defer writer.Flush()

	// Lê o cabeçalho
	header, err := reader.Read()
	if err != nil {
		log.Fatalf("Erro ao ler cabeçalho: %v", err)
	}

	cryptoNames := map[string]struct{}{}
	colIndices := map[string]map[string]int{}

	for i, col := range header {
		parts := strings.Split(col, "_")
		if col == "fear_api_alternative_me" || col == "fear_coinmarketcap" {
			continue
		} else if len(parts) == 2 {
			crypto, kind := parts[0], parts[1]
			cryptoNames[crypto] = struct{}{}
			if _, ok := colIndices[crypto]; !ok {
				colIndices[crypto] = map[string]int{}
			}
			colIndices[crypto][kind] = i
		}
	}

	// Escreve novo cabeçalho com colunas percentuais
	newHeader := append([]string{}, header...)
	for crypto := range cryptoNames {
		newHeader = append(newHeader, crypto+"_PercentHigh")
		newHeader = append(newHeader, crypto+"_PercentLow")
	}
	err = writer.Write(newHeader)
	if err != nil {
		log.Fatalf("Erro ao escrever cabeçalho no arquivo: %v", err)
	}

	// Lógica de comparação com a linha anterior
	var prevRecord []string

	for {
		record, err := reader.Read()
		if err != nil {
			break // EOF
		}
		newRecord := append([]string{}, record...)

		for crypto := range cryptoNames {
			indices := colIndices[crypto]

			highIdx, okHigh := indices["High"]
			lowIdx, okLow := indices["Low"]

			if okHigh {
				newRecord = processLine(highIdx, prevRecord, record, newRecord)
			} else {
				newRecord = append(newRecord, "")
			}

			if okLow {
				newRecord = processLine(lowIdx, prevRecord, record, newRecord)
			} else {
				newRecord = append(newRecord, "")
			}
		}

		err = writer.Write(newRecord)
		if err != nil {
			log.Fatalf("Erro ao escrever linha no arquivo: %v", err)
		}

		prevRecord = record
	}

	if err := writer.Error(); err != nil {
		log.Fatalf("Erro ao finalizar escrita: %v", err)
	}

	log.Printf("Dataset atualizado com percentuais baseados no Close do minuto anterior: %s", finalDatasetFilePath)
}

func processLine(idx int, prevRecord, record, newRecord []string) []string {
	if prevRecord == nil || idx >= len(prevRecord) || idx >= len(record) {
		return append(newRecord, "")
	}
	prevClose, err1 := strconv.ParseFloat(prevRecord[idx], 64)
	currClose, err2 := strconv.ParseFloat(record[idx], 64)
	if err1 != nil || err2 != nil || prevClose == 0 {
		return append(newRecord, "")
	}
	percent := ((currClose - prevClose) / prevClose) * 100.0
	return append(newRecord, strconv.FormatFloat(percent, 'f', 4, 64))
}
