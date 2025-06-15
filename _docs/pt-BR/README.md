# 🚀 Crypto Trader Bot

Scripts necessários para treinar o modelo de IA e executar o bot de trading automatizado em criptomoedas.

## 📌 Visão Geral

O **Crypto Trader Bot** é uma aplicação que utiliza aprendizado de máquina (machine learning) para prever movimentos do mercado de criptomoedas, com base na análise do **Fear & Greed Index** e em dados históricos de preços.

Os scripts são projetados para identificar correlações entre o índice de medo e o preço de cada criptoativo. O sistema pode operar de forma autônoma, executando estratégias baseadas em predições de mercado.

## 🛠️ Requisitos

Para usar este projeto, você pode optar por rodá-lo dentro de um **DevContainer (recomendado)** ou configurar manualmente em sua máquina. Abaixo estão os requisitos conforme sua escolha:

### ✅ Requisitos Gerais

* [Visual Studio Code (VSCode)](https://code.visualstudio.com/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop)
* [Extensão DevContainers para VSCode](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### ⚙️ Requisitos Locais (caso deseje rodar fora do container)

* [Go](https://golang.org/dl/) (versão 1.20 ou superior)
* [Python 3.10+](https://www.python.org/)

### 🚀 Suporte Opcional (CUDA)

* [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
  *Usado para acelerar o treinamento dos modelos via GPU (quando disponível).*

> 💡 A utilização de CUDA é **opcional**, mas recomendada se você deseja acelerar operações intensivas de machine learning usando sua GPU NVIDIA.

## 🧪 Tecnologias Usadas

* **Go** – Para coleta e persistência dos dados.
* **Python** – Para análise, modelagem e treinamento do modelo de IA.
* **SQLite** – Banco de dados leve e embutido.
* **Docker + DevContainers** – Ambiente isolado e reproduzível.
* **CUDA (Opcional)** – Aceleração com GPU da NVIDIA para treinar modelos mais rápido.

## 🚀 Como Começar

### 1. Clone o Repositório

```bash
git clone https://github.com/EliasJuniorNino/crypto-trader-bot.git
cd crypto-trader-bot
```

### 2. Configure Variáveis de Ambiente

Copie o arquivo `.env.example` e ajuste as configurações necessárias (APIs, caminhos, configurações do banco, etc.):

```bash
cp .env.example .env
```

O projeto utiliza um arquivo `.env` para armazenar chaves de API usadas para acessar dados da **Binance** e da **CoinMarketCap**.

| Variável                | Descrição                                                                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `COINMARKETCAP_API_KEY` | Sua chave da API da [CoinMarketCap](https://coinmarketcap.com/api/), usada para obter dados atualizados de capitalização de mercado, volume, rankings, etc. |
| `BINANCE_API_KEY`       | Chave pública da API da [Binance](https://www.binance.com/en/support/faq/360002502072) para acessar dados de preços, ordens e saldo.                        |
| `BINANCE_API_SECRET`    | Chave secreta da API da Binance, usada para autenticação e operações com a conta.                                                                           |

> 💡 Se você pretende apenas coletar dados públicos da Binance (como preços e volumes), as chaves `BINANCE_API_KEY` e `BINANCE_API_SECRET` podem ser deixadas em branco — mas são obrigatórias para ações como criação de ordens ou consulta de saldo.

> ⚠️ **Segurança**: Nunca compartilhe seu arquivo `.env`. Ele contém informações sensíveis e já está protegido pelo `.gitignore`.

## 🐳 Ambiente com DevContainers (Recomendado)

O projeto já vem preparado com um ambiente de desenvolvimento completo usando **Docker** e **DevContainers**, o que garante que todas as dependências de Go, Python e bibliotecas nativas estejam prontas para uso.

### ✅ Passos:

1. Instale o [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. Instale o [VSCode](https://code.visualstudio.com/)

3. Instale a extensão [DevContainers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) no VSCode

4. Abra o projeto no VSCode e pressione `F1` ou `Ctrl+Shift+P`, depois selecione:

   ```
   Dev Containers: Reopen in Container
   ```

5. Aguarde a construção automática do container com o ambiente completo (Go + Python + dependências)

> ⚠️ **Importante**: Tanto o ambiente **Go** quanto o **Python** devem ser configurados, pois o bot principal é escrito em Go, mas ele executa periodicamente scripts em Python para análise e modelagem. Ambos são necessários para o funcionamento completo do sistema.

6. Após carregado:

   * Execute o script de setup Python:

     ```bash
     cd python-project
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

   * Agora, você pode executar normalmente os scripts Python ou rodar o bot em Go:

     ```bash
     go run .
     ```

## ⚙️ Etapas Manuais (Se não quiser usar o container)

> ⚠️ **Importante**: Tanto o ambiente **Go** quanto o **Python** devem ser configurados, pois o bot principal é escrito em Go, mas ele executa periodicamente scripts em Python para análise e modelagem. Ambos são necessários para o funcionamento completo do sistema.

### Python

1. Navegue até a pasta de scripts em Python:

   ```bash
   cd python-project
   ```

2. Crie um ambiente virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Teste o script (opcional):

   ```bash
   python generate_models.py
   ```

### Go

1. Volte para a raiz do projeto (se ainda estiver em `python-project`):

   ```bash
   cd ..
   ```

2. Instale as dependências:

   ```bash
   go mod tidy
   ```

3. Execute o bot:

   ```bash
   go run .
   ```

## 🎁 Suporte a CUDA

Se você possui uma GPU NVIDIA com suporte a CUDA, o DevContainer pode aproveitar o poder da GPU para acelerar o treinamento dos modelos.

Requisitos:

* Instalar [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
* Usar o Docker com suporte a GPU
* Rodar com o seguinte comando:

```bash
docker compose --profile cuda up
```

## 📚 Documentação Completa

Para instruções detalhadas de uso, parâmetros disponíveis, exemplos de execução, estrutura dos scripts e mais, acesse a documentação completa do projeto:

👉 **[📖 Acessar Documentação do Projeto](USAGE.md)**

> O arquivo `USAGE.md` contém tudo o que você precisa para utilizar o bot corretamente, incluindo como treinar o modelo, configurar os parâmetros de entrada e executar o sistema em diferentes modos.

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
