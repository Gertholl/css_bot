#!/bin/sh

# Запускаем Certbot для получения сертификатов, если это необходимо
if [ ! -f /etc/letsencrypt/live/gerthollbots.ru/fullchain.pem ]; then
    certbot certonly --nginx --non-interactive --agree-tos --email gertholl1337@gmail.com -d gerthollbots.ru
fi

# Запускаем cron для автоматического обновления сертификатов
cron

# Запускаем Nginx
nginx -g 'daemon off;'

