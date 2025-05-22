package ui

import (
	"app/src/scripts/disableCryptos"
	"app/src/scripts/getBinanceData"
	"app/src/scripts/getDailyPrices"
	"app/src/scripts/getFearIndex"
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"
)

func MainCMD() {
	for {
		showMenu()
		choice := getUserChoice()

		switch choice {
		case "0":
			fmt.Println("\n👋 Saindo do programa...")
			os.Exit(0)
		case "1":
			fmt.Println("\n🔍 Executando GetFearCoinmarketcap...")
			getFearIndex.GetFearCoinmarketcap()
		case "2":
			fmt.Println("\n🔍 Executando GetFearAlternativeMe...")
			getFearIndex.GetFearAlternativeMe()
		case "3":
			fmt.Println("\n🔍 Executando GetBinanceCurrentDayCryptos...")
			getDailyPrices.Main()
		case "4":
			fmt.Println("\n🔍 Executando DownloadBinanceCryptoData...")
			getBinanceData.Main()
		case "5":
			fmt.Println("\n🔍 Executando DisableCryptos...")
			minDate, maxDate := getDateRange()
			disableCryptos.Main(minDate, maxDate)
		default:
			fmt.Println("\n❌ Opção inválida! Por favor, escolha uma opção válida.")
		}

		fmt.Println("\n" + strings.Repeat("-", 50))
	}
}

func showMenu() {
	fmt.Println("\n📊 CRYPTOTRADER - MENU PRINCIPAL")
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("0. 🚪 Sair")
	fmt.Println("1. 📈 GetFearCoinmarketcap")
	fmt.Println("2. 📈 GetFearAlternativeMe")
	fmt.Println("3. 📈 GetBinanceCurrentDayCryptos")
	fmt.Println("4. 📦 DownloadBinanceCryptoData")
	fmt.Println("5. 🔄 DisableCryptos")
	fmt.Println(strings.Repeat("=", 40))
	fmt.Print("Escolha uma opção: ")
}

func getUserChoice() string {
	var choice string
	fmt.Scanln(&choice)
	return choice
}

func getDateRange() (string, string) {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("\n📅 CONFIGURAÇÃO DE DATAS")
	fmt.Println(strings.Repeat("-", 30))

	// Obter data inicial
	var minDate string
	for {
		fmt.Print("📅 Digite a data inicial (YYYY-MM-DD): ")
		scanner.Scan()
		minDate = strings.TrimSpace(scanner.Text())

		if isValidDate(minDate) {
			break
		}
		fmt.Println("❌ Data inválida! Use o formato YYYY-MM-DD (ex: 2023-01-01)")
	}

	// Obter data final
	var maxDate string
	for {
		fmt.Print("📅 Digite a data final (YYYY-MM-DD): ")
		scanner.Scan()
		maxDate = strings.TrimSpace(scanner.Text())

		if isValidDate(maxDate) {
			// Verificar se a data final é posterior à inicial
			if isDateAfterOrEqual(maxDate, minDate) {
				break
			}
			fmt.Println("❌ A data final deve ser igual ou posterior à data inicial!")
		} else {
			fmt.Println("❌ Data inválida! Use o formato YYYY-MM-DD (ex: 2023-12-31)")
		}
	}

	fmt.Printf("✅ Período selecionado: %s até %s\n", minDate, maxDate)
	fmt.Println(strings.Repeat("-", 30))

	return minDate, maxDate
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
