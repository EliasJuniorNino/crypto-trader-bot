package main

import (
	"CryptoTrader/scripts"
	"fmt"
	"os"
	"strings"
)

func main() {
	scripts.GetBinanceCurrentDayCryptos()
	for {
		showMenu()
		choice := getUserChoice()

		switch choice {
		case "0":
			fmt.Println("\n👋 Saindo do programa...")
			os.Exit(0)
		case "1":
			fmt.Println("\n🔍 Executando GetFearCoinmarketcap...")
			scripts.GetFearCoinmarketcap()
		case "2":
			fmt.Println("\n🔍 Executando GetFearAlternativeMe...")
			scripts.GetFearAlternativeMe()
		case "3":
			fmt.Println("\n🔍 Executando GetBinanceCurrentDayCryptos...")
			scripts.GetBinanceCurrentDayCryptos()
		case "4":
			fmt.Println("\n🔍 Executando DownloadBinanceCryptoData...")
			scripts.DownloadBinanceCryptoData()
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
	fmt.Println("3. 📉 GetBinanceCurrentDayCryptos")
	fmt.Println("4. 📉 DownloadBinanceCryptoData")
	fmt.Println(strings.Repeat("=", 40))
	fmt.Print("Escolha uma opção: ")
}

func getUserChoice() string {
	var choice string
	fmt.Scanln(&choice)
	return choice
}
