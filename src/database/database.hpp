// banco.hpp - Interface para conexão SQLite (adaptado do database.ConnectDatabase do Go)
#pragma once
#include <sqlite3.h>
#include <string>
#include <stdexcept>

inline sqlite3* connectDatabase(const std::string& path = "app.db") {
    sqlite3* db = nullptr;
    if (sqlite3_open(path.c_str(), &db) != SQLITE_OK) {
        throw std::runtime_error("Erro ao conectar ao banco de dados");
    }
    return db;
}
