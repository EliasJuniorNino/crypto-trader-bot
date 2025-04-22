#!/bin/bash

# Configurações do banco de dados
TIMESTAMP=$(date +"%F-%H-%M")
CONTAINER_NAME="mySQL"
DB_USER="root"
DB_PASSWORD="root_password"
DB_NAME="database"
BACKUP_DIR="/backups"

# Criar diretório de backup caso não exista
mkdir -p $BACKUP_DIR

# Realiza o dump do banco de dados
docker exec $CONTAINER_NAME mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

# Apagar backups antigos (mais de 7 dias)
find $BACKUP_DIR -type f -name "*.sql" -mtime +7 -delete
