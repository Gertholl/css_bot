# Используем официальный образ Nginx
FROM nginx:latest

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y certbot python3-certbot-nginx cron

# Копируем конфигурационные файлы
#COPY nginx.conf /etc/nginx/nginx.conf
#COPY server.conf /etc/nginx/conf.d/server.conf
COPY entrypoint.sh /entrypoint.sh
COPY cronjob /etc/cron.d/certbot-renew

# Устанавливаем права на выполнение для entrypoint.sh и cronjob
RUN chmod +x /entrypoint.sh && \
    chmod 0644 /etc/cron.d/certbot-renew && \
    crontab /etc/cron.d/certbot-renew

# Запускаем entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

