#!/bin/bash

# Liveness Detection Server
# Usage: ./run.sh [dev|prod|setup]

MODE=${1:-dev}
DOMAIN=${2:-"face-check.das-uty.uz"}
PORT=8001

echo "================================================"
echo "  Liveness Detection Server"
echo "================================================"
echo ""

# Setup - nginx + SSL + systemd avtomatik sozlash
if [ "$MODE" == "setup" ]; then
    echo "[1/5] Paketlarni o'rnatish..."
    pip install -r requirements.txt

    echo "[2/5] Nginx config yozish..."
    sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null <<NGINX
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:$PORT/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
NGINX

    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx sozlandi!"

    echo "[3/5] SSL sertifikat o'rnatish (Let's Encrypt)..."
    sudo apt install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || echo "SSL xato - qo'lda o'rnating: sudo certbot --nginx -d $DOMAIN"

    echo "[4/5] Systemd service yaratish..."
    WORKDIR=$(pwd)
    sudo tee /etc/systemd/system/liveness.service > /dev/null <<SERVICE
[Unit]
Description=Liveness Detection Server
After=network.target

[Service]
User=$USER
WorkingDirectory=$WORKDIR
ExecStart=$(which gunicorn) app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:$PORT
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable liveness
    sudo systemctl start liveness

    echo "[5/5] Tayyor!"
    echo ""
    echo "================================================"
    echo "  Server ishga tushdi!"
    echo "  URL: https://$DOMAIN"
    echo "  Test: https://$DOMAIN/test"
    echo ""
    echo "  Boshqarish:"
    echo "    sudo systemctl status liveness"
    echo "    sudo systemctl restart liveness"
    echo "    sudo systemctl stop liveness"
    echo "    sudo journalctl -u liveness -f"
    echo "================================================"
    exit 0
fi

if [ "$MODE" == "prod" ]; then
    echo "Production mode - 4 workers"
    gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
else
    echo "Development mode - auto-reload enabled"
    uvicorn app:app --host 0.0.0.0 --port $PORT --reload
fi
