#!/bin/bash

# Criar o diretório de build, se não existir
mkdir -p .build

# Compilar com suporte a C++17 e mensagens de erro claras
g++ -std=c++17 generate_dataset.cpp -o .build/generate -lmysqlcppconn -lboost_system -lboost_thread

# Verificar se a compilação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Compilação bem-sucedida. Executando..."
    ./.build/generate
else
    echo "Erro na compilação."
fi
