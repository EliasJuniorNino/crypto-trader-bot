-- Tabela de criptomoedas
CREATE TABLE IF NOT EXISTS cryptos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL,
    name VARCHAR(255) NULL,
    is_enabled TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE (symbol)
);

-- Tabela de exchanges
CREATE TABLE IF NOT EXISTS exchanges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NULL,
    UNIQUE (name)
);

-- Tabela de associação entre exchanges e criptomoedas
CREATE TABLE IF NOT EXISTS exchanges_cryptos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crypto_id INT NOT NULL,
    exchange_id INT NOT NULL,
    is_enabled TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE (crypto_id, exchange_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptos(id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE
);

-- Tabela do índice de medo e ganância
CREATE TABLE IF NOT EXISTS fear_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    target VARCHAR(255) NULL,
    date DATETIME NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    UNIQUE (source, target, date)
);

-- Tabela de trades realizados
CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(255) NULL,
    operation VARCHAR(255) NULL,
    quantity DECIMAL(10,4) NOT NULL,
    price_usd DECIMAL(10,4) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
