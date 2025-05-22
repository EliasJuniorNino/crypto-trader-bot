# 📖 Usage Guide – Crypto Trader Bot

This guide explains how to use the main application of **Crypto Trader Bot**, including descriptions of the menu options, what each script does, and which parameters are expected (when necessary).

---

## 🚀 Running the Bot

You can start the bot via terminal by running the command from the project root:

```bash
go run .
```

An interactive menu like this will be displayed:

```
📊 CRYPTOTRADER - MAIN MENU
========================================
0. 🚪 Exit
1. 📈 GetFearCoinmarketcap
2. 📈 GetFearAlternativeMe
3. 📈 GetBinanceCurrentDayCryptos
4. 📦 DownloadBinanceCryptoData
5. 🔄 DisableCryptos
========================================
Choose an option:
```

---

## 📋 Available Options

### 1. 📈 GetFearCoinmarketcap

Runs the collection of the **Fear & Greed Index** via CoinMarketCap. This option is useful for market sentiment analysis using data provided by this platform.

* **Prerequisite:** the variable `COINMARKETCAP_API_KEY` must be set in the `.env` file.

---

### 2. 📈 GetFearAlternativeMe

Runs the collection of the **Fear & Greed Index** via [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/). It is an alternative source of market sentiment, used as a basis for forecasting models.

---

### 3. 📈 GetBinanceCurrentDayCryptos

Collects all crypto assets listed on Binance for the **current day**. Useful to keep the database updated with assets available for analysis or trading operations.

---

### 4. 📦 DownloadBinanceCryptoData

Downloads historical price data (*Klines*) for the listed crypto assets. This data is used to train AI models and perform market analysis.

---

### 5. 🔄 DisableCryptos

Disables crypto assets that **do not have sufficient data** for the selected period. It checks if each crypto asset has data for at least one of the dates in the range. Otherwise, it will be disabled.

#### 🗓️ Required Parameters

You will be asked to provide:

* **Start Date** (`YYYY-MM-DD`)
* **End Date** (`YYYY-MM-DD`)

📌 Example of interactive use:

```
📅 Enter the start date (YYYY-MM-DD): 2023-01-01
📅 Enter the end date (YYYY-MM-DD): 2023-12-31
✅ Selected period: 2023-01-01 to 2023-12-31
```

---

## 🗃️ Data Storage

* The **collected data** is stored in the `data/` folder.
* The **trained models** are saved in the `models/` folder.
* A **SQLite database**, located in the project root, stores information such as:

  * List of enabled/disabled crypto assets
  * Market sentiment indices (fear index)
  * Other system settings and metadata

---

## ❓ Support

If you need additional help, please consult:

* The technical documentation in the source code itself
* Or open an *issue* in the [official repository](https://github.com/EliasJuniorNino/crypto-trader-bot)
