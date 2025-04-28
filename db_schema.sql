CREATE TABLE IF NOT EXISTS cryptos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL,
    name VARCHAR(255) NULL,
    UNIQUE (symbol)
);

CREATE TABLE IF NOT EXISTS exchanges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS exchanges_cryptos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crypto_id INT NOT NULL,
    exchange_id INT NOT NULL,
    UNIQUE (crypto_id, exchange_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptos(id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cryptos_price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    price DECIMAL(38,18) NOT NULL,
    crypto_id INT NOT NULL,
    exchange_id INT NOT NULL,
    UNIQUE (date, crypto_id, exchange_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptos(id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE
);
ALTER TABLE cryptos_price_history
ADD COLUMN open_time BIGINT NOT NULL,
ADD COLUMN open_price DECIMAL(38,18) NOT NULL,
ADD COLUMN high_price DECIMAL(38,18) NOT NULL,
ADD COLUMN low_price DECIMAL(38,18) NOT NULL,
ADD COLUMN close_price DECIMAL(38,18) NOT NULL,
ADD COLUMN volume DECIMAL(38,18) NOT NULL,
ADD COLUMN close_time BIGINT NOT NULL,
ADD COLUMN base_asset_volume DECIMAL(38,18) NOT NULL,
ADD COLUMN number_of_trades INT NOT NULL,
ADD COLUMN taker_buy_volume DECIMAL(38,18) NOT NULL,
ADD COLUMN taker_buy_base_asset_volume DECIMAL(38,18) NOT NULL;

CREATE TABLE IF NOT EXISTS fear_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    target VARCHAR(255) NULL,
    date DATETIME NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    UNIQUE (source, target, date)
);

ALTER TABLE cryptos_price_history
ADD COLUMN open_time BIGINT NOT NULL,
ADD COLUMN open_price DECIMAL(38,18) NOT NULL,
ADD COLUMN high_price DECIMAL(38,18) NOT NULL,
ADD COLUMN low_price DECIMAL(38,18) NOT NULL,
ADD COLUMN close_price DECIMAL(38,18) NOT NULL,
ADD COLUMN volume DECIMAL(38,18) NOT NULL,
ADD COLUMN close_time BIGINT NOT NULL,
ADD COLUMN base_asset_volume DECIMAL(38,18) NOT NULL,
ADD COLUMN number_of_trades INT NOT NULL,
ADD COLUMN taker_buy_volume DECIMAL(38,18) NOT NULL,
ADD COLUMN taker_buy_base_asset_volume DECIMAL(38,18) NOT NULL;

ALTER TABLE exchanges_cryptos
ADD COLUMN is_enabled TINYINT(1) NOT NULL DEFAULT 1;

ALTER TABLE cryptos
ADD COLUMN is_enabled TINYINT(1) NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(255) NULL,
    operation VARCHAR(255) NULL,
    quantity DECIMAL(10,4) NOT NULL,
    price_usd DECIMAL(10,4) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);