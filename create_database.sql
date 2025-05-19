-- Cria a tabela de criptomoedas
DROP TABLE IF EXISTS cryptos;
CREATE TABLE IF NOT EXISTS cryptos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT,
    is_enabled INTEGER DEFAULT 1
);

-- Cria a tabela de exchanges
DROP TABLE IF EXISTS exchanges;
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_enabled INTEGER DEFAULT 1
);

-- Tabela de relacionamento entre exchanges e criptomoedas
DROP TABLE IF EXISTS exchanges_cryptos;
CREATE TABLE IF NOT EXISTS exchanges_cryptos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_id INTEGER NOT NULL,
    crypto_id INTEGER NOT NULL,
    is_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
    FOREIGN KEY (crypto_id) REFERENCES cryptos(id),
    UNIQUE (exchange_id, crypto_id)
);
