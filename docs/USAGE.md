# 📖 Guia de Uso – Crypto Trader Bot

Este guia explica como utilizar a aplicação principal do **Crypto Trader Bot**, incluindo a descrição das opções do menu, o que cada script faz e quais parâmetros são esperados (quando necessário).

---

## 🚀 Executando o Bot

Você pode iniciar o bot via terminal executando o comando a partir da raiz do projeto:

```bash
go run .
```

Será exibido um menu interativo como este:

```
📊 CRYPTOTRADER - MENU PRINCIPAL
========================================
0. 🚪 Sair
1. 📈 GetFearCoinmarketcap
2. 📈 GetFearAlternativeMe
3. 📈 GetBinanceCurrentDayCryptos
4. 📦 DownloadBinanceCryptoData
5. 🔄 DisableCryptos
========================================
Escolha uma opção:
```

---

## 📋 Opções Disponíveis

### 1. 📈 GetFearCoinmarketcap

Executa a coleta do **Fear & Greed Index** via CoinMarketCap. Essa opção é útil para análises de sentimento de mercado com dados fornecidos por esta plataforma.

* **Pré-requisito:** a variável `COINMARKETCAP_API_KEY` deve estar definida no arquivo `.env`.

---

### 2. 📈 GetFearAlternativeMe

Executa a coleta do **Fear & Greed Index** via [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/). É uma fonte alternativa de sentimento de mercado, usada como base para modelos de previsão.

---

### 3. 📈 GetBinanceCurrentDayCryptos

Coleta todos os criptoativos listados na Binance no **dia atual**. Útil para manter a base de dados atualizada com os ativos disponíveis para análise ou operações de trading.

---

### 4. 📦 DownloadBinanceCryptoData

Baixa dados históricos de preços (*Klines*) para os criptoativos listados. Esses dados são usados para treinar modelos de IA e realizar análises de mercado.

---

### 5. 🔄 DisableCryptos

Desativa criptoativos que **não possuem dados suficientes** para o período selecionado. Verifica se cada criptoativo possui dados para pelo menos uma das datas do intervalo. Caso contrário, ele será desativado..

#### 🗓️ Parâmetros Requeridos

Você será solicitado a informar:

* **Data Inicial** (`YYYY-MM-DD`)
* **Data Final** (`YYYY-MM-DD`)



📌 Exemplo de uso interativo:

```
📅 Digite a data inicial (YYYY-MM-DD): 2023-01-01
📅 Digite a data final (YYYY-MM-DD): 2023-12-31
✅ Período selecionado: 2023-01-01 até 2023-12-31
```

---

## 🗃️ Armazenamento de Dados

* Os **dados coletados** são armazenados na pasta `data/`.
* Os **modelos treinados** são salvos na pasta `models/`.
* Um **banco de dados SQLite**, localizado na raiz do projeto, armazena informações como:

  * Lista de criptoativos habilitados/desabilitados
  * Índices de sentimento de mercado (fear index)
  * Outras configurações e metadados do sistema

---

## ❓ Suporte

Se precisar de ajuda adicional, consulte:

* A documentação técnica no próprio código-fonte
* Ou abra uma *issue* no [repositório oficial](https://github.com/EliasJuniorNino/crypto-trader-bot)

---

Se quiser, posso gerar um arquivo `USAGE.md` já formatado com esse conteúdo. Deseja que eu faça isso agora?
