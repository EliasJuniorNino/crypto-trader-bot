#!/bin/bash

# Script para carregar variáveis do arquivo .env e configurar o Git

# Definindo cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configurando Git a partir do arquivo .env...${NC}"

# Verificando se o arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${RED}Erro: Arquivo .env não encontrado!${NC}"
    exit 1
fi

# Carregando variáveis do arquivo .env de forma segura (preservando espaços)
echo -e "${YELLOW}Carregando variáveis do arquivo .env...${NC}"
# Usando while read para preservar espaços nos valores
while IFS= read -r line || [[ -n "$line" ]]; do
    # Ignorar linhas em branco ou comentários
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Exportar a variável preservando os espaços
    export "$line"
done < .env

# Verificando se as variáveis necessárias foram definidas
if [ -z "$GIT_USER_NAME" ] || [ -z "$GIT_USER_EMAIL" ]; then
    echo -e "${RED}Erro: GIT_USER_NAME ou GIT_USER_EMAIL não definidos no arquivo .env!${NC}"
    echo -e "${YELLOW}Por favor, adicione as seguintes linhas ao seu arquivo .env:${NC}"
    echo "GIT_USER_NAME=Seu Nome Completo"
    echo "GIT_USER_EMAIL=seu.email@exemplo.com"
    exit 1
fi

# Configurando o Git
echo -e "${YELLOW}Configurando Git com:${NC}"
echo -e "  Username: ${GREEN}$GIT_USER_NAME${NC}"
echo -e "  Email: ${GREEN}$GIT_USER_EMAIL${NC}"

git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
git config --global --add safe.directory /workspaces/CryptoTrader

# Verificando se a configuração foi bem-sucedida
CONFIGURED_NAME=$(git config --global user.name)
CONFIGURED_EMAIL=$(git config --global user.email)

echo -e "${YELLOW}Verificando configuração:${NC}"
echo -e "  Nome configurado: ${GREEN}$CONFIGURED_NAME${NC}"
echo -e "  Email configurado: ${GREEN}$CONFIGURED_EMAIL${NC}"

if [ "$CONFIGURED_NAME" = "$GIT_USER_NAME" ] && [ "$CONFIGURED_EMAIL" = "$GIT_USER_EMAIL" ]; then
    echo -e "${GREEN}Configuração do Git concluída com sucesso!${NC}"
    echo -e "${YELLOW}Configurações atuais do Git:${NC}"
    echo -e "$(git config --list | grep user)"
else
    echo -e "${RED}Aviso: Os valores configurados podem não corresponder exatamente aos valores no arquivo .env.${NC}"
    echo -e "${YELLOW}Configurações atuais do Git:${NC}"
    echo -e "$(git config --list | grep user)"
fi

echo -e "\n${GREEN}Script concluído.${NC}"