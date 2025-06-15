[🇺🇸 English](README.md) | [🇧🇷 Português](docs/pt-BR/README.md)

# 🚀 Crypto Trader Bot

Scripts required to train the AI model and run the automated cryptocurrency trading bot.

## 📌 Overview

**Crypto Trader Bot** is an application that uses machine learning to predict cryptocurrency market movements based on analysis of the **Fear & Greed Index** and historical price data.

The scripts are designed to identify correlations between the fear index and the price of each crypto asset. The system can operate autonomously, executing strategies based on market predictions.

## 🛠️ Requirements

To use this project, you can choose to run it inside a **DevContainer (recommended)** or set it up manually on your local machine. Below are the requirements depending on your choice:

### ✅ General Requirements

* [Visual Studio Code (VSCode)](https://code.visualstudio.com/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop)
* [DevContainers Extension for VSCode](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### ⚙️ Local Setup Requirements (if you prefer not to use containers)

* [Go](https://golang.org/dl/) (version 1.20 or higher)
* [Python 3.10+](https://www.python.org/)

### 🚀 Optional Support (CUDA)

* [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
  *Used to speed up model training via GPU (if available).*

> 💡 CUDA usage is **optional**, but recommended if you want to accelerate heavy machine learning operations using your NVIDIA GPU.

## 🧪 Technologies Used

* **Go** – For data collection and persistence.
* **Python** – For analysis, modeling, and AI training.
* **SQLite** – Lightweight embedded database.
* **Docker + DevContainers** – Isolated and reproducible development environment.
* **CUDA (Optional)** – NVIDIA GPU acceleration for faster model training.

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/EliasJuniorNino/crypto-trader-bot.git
cd crypto-trader-bot
```

### 2. Configure Environment Variables

Copy the `.env.example` file and adjust the necessary settings (APIs, paths, database config, etc.):

```bash
cp .env.example .env
```

The project uses a `.env` file to store API keys used to access **Binance** and **CoinMarketCap** data.

| Variable                | Description                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `COINMARKETCAP_API_KEY` | Your [CoinMarketCap](https://coinmarketcap.com/api/) API key, used to fetch market cap data, volume, rankings, etc.            |
| `BINANCE_API_KEY`       | Public API key from [Binance](https://www.binance.com/en/support/faq/360002502072), used for price data, orders, and balances. |
| `BINANCE_API_SECRET`    | Secret Binance API key, used for authentication and account operations.                                                        |

> 💡 If you're only collecting public data from Binance (such as prices and volumes), the `BINANCE_API_KEY` and `BINANCE_API_SECRET` can be left empty — but they are required for actions like placing orders or checking balances.

> ⚠️ **Security**: Never share your `.env` file. It contains sensitive information and is already protected via `.gitignore`.

## 🐳 DevContainer Environment (Recommended)

This project is fully prepared for a **Docker + DevContainer** environment, which ensures all Go, Python, and native library dependencies are ready to use.

### ✅ Steps:

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. Install [VSCode](https://code.visualstudio.com/)

3. Install the [DevContainers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) in VSCode

4. Open the project in VSCode and press `F1` or `Ctrl+Shift+P`, then select:

   ```
   Dev Containers: Reopen in Container
   ```

5. Wait for the container to be automatically built with the complete environment (Go + Python + dependencies)

> ⚠️ **Important**: Both **Go** and **Python** environments must be set up, as the main bot is written in Go, but periodically executes Python scripts for analysis and modeling. Both are required for full system functionality.

6. After setup is complete:

   * Run the Python setup script:

     ```bash
     cd python-project
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

   * Now, you can run the Python scripts or start the Go bot:

     ```bash
     go run .
     ```

## ⚙️ Manual Setup (If not using containers)

> ⚠️ **Important**: Both **Go** and **Python** environments must be configured, as the main bot is written in Go and depends on Python scripts for analysis and modeling.

### Python

1. Navigate to the Python scripts folder:

   ```bash
   cd python-project
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Test a script (optional):

   ```bash
   python generate_models.py
   ```

### Go

1. Return to the project root (if you're still in `python-project`):

   ```bash
   cd ..
   ```

2. Install Go dependencies:

   ```bash
   go mod tidy
   ```

3. Run the bot:

   ```bash
   go run .
   ```

## 🎁 CUDA Support

If you have an NVIDIA GPU with CUDA support, the DevContainer can leverage GPU power to speed up model training.

Requirements:

* Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
* Use Docker with GPU support
* Run using the following command:

```bash
docker compose --profile cuda up
```

## 📚 Full Documentation

For detailed usage instructions, available parameters, execution examples, script structure, and more, check out the full project documentation:

👉 **[📖 View Project Documentation](./_docs/en/USAGE.md)**

> The `USAGE.md` file contains everything you need to use the bot properly, including how to train the model, configure input parameters, and run the system in different modes.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
