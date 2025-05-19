# Etapa base com suporte a Node.js e Python + TensorFlow
FROM python:3.9-slim

# Instala Node.js LTS (18.x) + dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    python3-dev \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

# Cria diretório da aplicação
WORKDIR /app

# Copia arquivos do projeto
COPY . /app

# Instala dependências Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala dependências Node.js
RUN npm install

# Expõe a porta do Jupyter caso queira usá-lo futuramente
EXPOSE 8888

# Comando padrão (pode ser sobrescrito no docker-compose)
CMD ["node", "trader.js"]
