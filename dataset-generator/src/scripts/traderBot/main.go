package traderBot

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/adshao/go-binance/v2"
)

func Main() {
	apiKey := os.Getenv("BINANCE_API_KEY")
	secretKey := os.Getenv("BINANCE_API_SECRET")

	client := binance.NewClient(apiKey, secretKey)

	symbol := "BTCUSDT"
	quantity := 0.001

	for {
		err := tradeLogic(client, symbol, quantity)
		if err != nil {
			log.Println("Erro na estratégia:", err)
		}
		time.Sleep(1 * time.Minute)
	}
}

func tradeLogic(client *binance.Client, symbol string, quantity float64) error {
	klines, err := client.NewKlinesService().
		Symbol(symbol).
		Interval("1m").
		Limit(2).
		Do(context.Background())
	if err != nil {
		return fmt.Errorf("erro ao obter Klines: %v", err)
	}

	prevClose, _ := strconv.ParseFloat(klines[0].Close, 64)
	lastClose, _ := strconv.ParseFloat(klines[1].Close, 64)

	change := (lastClose - prevClose) / prevClose * 100
	fmt.Printf("Preço anterior: %.2f, atual: %.2f, variação: %.2f%%\n", prevClose, lastClose, change)

	if change <= -0.5 {
		fmt.Println("🔽 Queda detectada. Comprando...")
		return executeOrder(client, symbol, quantity, binance.SideTypeBuy)
	} else if change >= 0.5 {
		fmt.Println("🔼 Alta detectada. Vendendo...")
		return executeOrder(client, symbol, quantity, binance.SideTypeSell)
	} else {
		fmt.Println("⏸ Sem ação no momento.")
	}

	return nil
}

func executeOrder(client *binance.Client, symbol string, quantity float64, side binance.SideType) error {
	order, err := client.NewCreateOrderService().
		Symbol(symbol).
		Side(side).
		Type(binance.OrderTypeMarket).
		Quantity(fmt.Sprintf("%f", quantity)).
		Do(context.Background())
	if err != nil {
		return fmt.Errorf("erro ao executar ordem: %v", err)
	}

	fmt.Println("✅ Ordem executada:", order)
	return nil
}
