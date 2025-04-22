# Baseado na imagem alpine
FROM alpine:latest

# Atualiza os repositórios e instala bash, dcron e mysql-client
RUN apk update && apk add --no-cache bash dcron mysql-client

# Copia o script de backup
COPY backup.sh /backup.sh

# Torna o script executável
RUN chmod +x /backup.sh

# Configura o cron job para rodar às 2h da manhã todos os dias
RUN echo "0 2 * * * /backup.sh >> /backups/cron.log 2>&1" > /etc/crontabs/root

# Inicia o dcron (cron) em primeiro plano
CMD ["dcron", "-f"]
