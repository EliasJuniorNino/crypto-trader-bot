# Crypto Trader Bot

Um bot de trading automatizado para criptomoedas, desenvolvido com foco em aprendizado e experimentação.  
Este projeto integra diversas tecnologias para operar no mercado de criptomoedas de forma autônoma.

## 📌 Visão Geral

O **Crypto Trader Bot** é uma aplicação que visa automatizar operações de compra e venda de criptomoedas.  
Utilizando APIs de exchanges, o bot analisa o mercado e executa ordens com base em estratégias predefinidas.

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
