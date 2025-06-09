package main

import (
	"app/src/scripts/disableCryptos"
	"app/src/scripts/generateDataset"
	"app/src/scripts/generateModels"
	"app/src/scripts/getBinanceData"
	"app/src/scripts/getDailyPrices"
	"app/src/scripts/getFearIndex"
	"app/src/ui"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"
)

func main() {
	// Definição das flags
	showHelp := flag.Bool("h", false, "Exibe o menu de ajuda")
	fearCMC := flag.Bool("GetFearCoinmarketcap", false, "Executa GetFearCoinmarketcap")
	fearAltMe := flag.Bool("GetFearAlternativeMe", false, "Executa GetFearAlternativeMe")
	getBinance := flag.Bool("GetBinanceCurrentDayCryptos", false, "Executa GetBinanceCurrentDayCryptos")
	downloadBinance := flag.Bool("DownloadBinanceCryptoData", false, "Executa DownloadBinanceCryptoData")
	getAllCryptos := flag.Bool("GetAllCryptos", false, "Busca todas as criptomoedas")
	disableCryptosFlag := flag.Bool("DisableCryptos", false, "Executa DisableCryptos")
	resetCurrentDataset := flag.Bool("ResetCurrentDataset", false, "Subistitui o dataset atual")
	generateDatasetFlag := flag.Bool("GenerateDataset", false, "Executa GenerateDataset")
	generateModelsFlag := flag.Bool("GenerateModels", false, "Executa GenerateModels")
	start := flag.String("start", "", "Data inicial (YYYY-MM-DD) para DisableCryptos")
	end := flag.String("end", "", "Data final (YYYY-MM-DD) para DisableCryptos")

	flag.Parse()

	// Mostra ajuda se solicitado ou se nenhuma flag principal for passada
	if len(os.Args) == 1 {
		ui.MainCMD()
		return
	}

	// Controle de execução múltipla:
	executouAlgum := false

	if *showHelp {
		showUsage()
		executouAlgum = true
	}

	if *fearCMC {
		fmt.Println("🔍 Executando GetFearCoinmarketcap...")
		getFearIndex.GetFearCoinmarketcap()
		executouAlgum = true
	}

	if *fearAltMe {
		fmt.Println("🔍 Executando GetFearAlternativeMe...")
		getFearIndex.GetFearAlternativeMe()
		executouAlgum = true
	}

	if *getBinance {
		fmt.Println("🔍 Executando GetBinanceCurrentDayCryptos...")
		getDailyPrices.Main()
		executouAlgum = true
	}

	if *downloadBinance {
		fmt.Println("🔍 Executando DownloadBinanceCryptoData...")
		getBinanceData.Main(*getAllCryptos)
		executouAlgum = true
	}

	if *generateDatasetFlag {
		fmt.Println("🔍 Executando GenerateDataset...")
		if *start == "" || *end == "" {
			fmt.Println("❌ Para usar -GenerateDataset, forneça -start e -end no formato YYYY-MM-DD.")
			return
		}
		startDate, err := time.Parse("2006-01-02", *start)
		if err != nil {
			fmt.Println("❌ Erro ao converter data inicial:", err)
			return
		}
		endDate, err := time.Parse("2006-01-02", *end)
		if err != nil {
			fmt.Println("❌ Erro ao converter data final:", err)
			return
		}
		generateDataset.Main(startDate, endDate, *resetCurrentDataset)
		executouAlgum = true
	}

	if *generateModelsFlag {
		generateModels.Main()
		executouAlgum = true
	}

	if *disableCryptosFlag {
		if *start == "" || *end == "" {
			fmt.Println("❌ Para usar -DisableCryptos, forneça -start e -end no formato YYYY-MM-DD.")
			return
		}

		if !isValidDate(*start) || !isValidDate(*end) || !isDateAfterOrEqual(*end, *start) {
			fmt.Println("❌ Datas inválidas. Use o formato YYYY-MM-DD e certifique-se de que a data final seja igual ou posterior à inicial.")
			return
		}

		fmt.Printf("🔄 Executando DisableCryptos de %s até %s...\n", *start, *end)
		disableCryptos.Main(*start, *end)
		executouAlgum = true
	}

	if !executouAlgum {
		fmt.Println("❌ Nenhuma opção reconhecida. Use -h para ver os comandos disponíveis.")
	}
}

func showUsage() {
	fmt.Println("\n📊 CRYPTOTRADER - CLI (sem interação)")
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("Uso:")
	fmt.Println("  main.exe [OPÇÃO] [FLAGS OPCIONAIS]")
	fmt.Println()
	fmt.Println("Opções:")
	fmt.Println("  -h                            → Exibe este menu")
	fmt.Println("  -GetFearCoinmarketcap        → Executa GetFearCoinmarketcap")
	fmt.Println("  -GetFearAlternativeMe        → Executa GetFearAlternativeMe")
	fmt.Println("  -GetBinanceCurrentDayCryptos → Executa GetBinanceCurrentDayCryptos")
	fmt.Println("  -DownloadBinanceCryptoData   → Executa DownloadBinanceCryptoData")
	fmt.Println("  -DisableCryptos              → Executa DisableCryptos (necessita -start e -end)")
	fmt.Println("  -GenerateDataset             → Executa GenerateDataset")
	fmt.Println()
	fmt.Println("Exemplo:")
	fmt.Println("  main.exe -DisableCryptos -start 2024-01-01 -end 2024-12-31")
	fmt.Println(strings.Repeat("=", 40))
}

func isValidDate(dateStr string) bool {
	_, err := time.Parse("2006-01-02", dateStr)
	return err == nil
}

func isDateAfterOrEqual(date1, date2 string) bool {
	d1, err1 := time.Parse("2006-01-02", date1)
	d2, err2 := time.Parse("2006-01-02", date2)
	if err1 != nil || err2 != nil {
		return false
	}
	return d1.After(d2) || d1.Equal(d2)
}
