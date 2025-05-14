# Crypto Trader Bot

Scripts required to train the AI model and run the automated trading bot.

## 📌 Overview

The **Crypto Trader Bot** is an application that uses machine learning to predict cryptocurrency market movements based on the analysis of the Fear Index and historical price data.  
The scripts are designed to find a correlation between the **Fear Index** and the price of each cryptocurrency.

## ⚙️ Technologies Used

- **Python**
- **JavaScript (Node.js)**
- **C++**
- **Docker**
- **Shell Script**

## 📁 Project Structure

The project is organized as follows:

```
crypto-trader-bot/
├── .devcontainer/         # Development environment configurations
├── .github/               # GitHub workflows and configurations
├── .vscode/               # Visual Studio Code configurations
├── scripts/               # Helper scripts
├── backup.sh              # Backup script
├── db_schema.sql          # Database schema
├── docker-compose.yml     # Docker Compose configuration
├── package.json           # Node.js dependencies
├── requirements.txt       # Python dependencies
└── ...                    # Other files and directories
```

## 🚀 How to Get Started

To run the bot locally:

1. Clone the repository:

   ```bash
   git clone https://github.com/EliasJuniorNino/crypto-trader-bot.git
   cd crypto-trader-bot
   ```

2. Configure the necessary environment variables.

3. Start the containers with Docker Compose:

   ```bash
   docker-compose up --build
   ```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
