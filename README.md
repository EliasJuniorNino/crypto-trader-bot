# Crypto Trader Bot

Códigos necessário para treinar o modelo de IA e executar o bot de trading automatizado.

## 📌 Visão Geral

O **Crypto Trader Bot** é uma aplicação que utiliza aprendizado de máquina para prever movimentos do mercado de criptomoedas com base na análise do índice de medo (Fear Index) e dados históricos de preços.  
Com base nessa correlação, o bot executa ordens de compra e venda de forma autônoma.

## ⚙️ Tecnologias Utilizadas

- **Python**
- **JavaScript (Node.js)**
- **C++**
- **Docker**
- **Shell Script**

## 📁 Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
crypto-trader-bot/
├── .devcontainer/         # Configurações para ambiente de desenvolvimento
├── .github/               # Workflows e configurações do GitHub
├── .vscode/               # Configurações do Visual Studio Code
├── scripts/               # Scripts auxiliares
├── backup.sh              # Script de backup
├── db_schema.sql          # Esquema do banco de dados
├── docker-compose.yml     # Configuração do Docker Compose
├── package.json           # Dependências do Node.js
├── requirements.txt       # Dependências do Python
└── ...                    # Outros arquivos e diretórios
```

## 🚀 Como Iniciar

Para executar o bot localmente:

1. Clone o repositório:

   ```bash
   git clone https://github.com/EliasJuniorNino/crypto-trader-bot.git
   cd crypto-trader-bot
   ```

2. Configure as variáveis de ambiente necessárias.

3. Inicie os containers com Docker Compose:

   ```bash
   docker-compose up --build
   ```

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.
