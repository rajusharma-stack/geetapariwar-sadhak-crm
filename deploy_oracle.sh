#!/bin/bash
set -e

APP_DIR="/home/ubuntu/Geetapariwarsadhak"
REPO_URL="https://github.com/rajusharma-stack/geetapariwar-sadhak-crm.git"
SERVICE_NAME="geetapariwar"

echo "=== Deploying Geeta Pariwar CRM ==="

# Create app directory if not exists
if [ ! -d "$APP_DIR" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

# Stash any local changes and pull latest
git stash || true
git pull origin master || git pull origin main

# Create data directory if not exists
mkdir -p data backups exports

# Setup virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

# Generate secret key if not set
if [ ! -f .secret_key ]; then
    echo "Generating secret key..."
    python3 -c "import secrets; print(secrets.token_hex(32))" > .secret_key
fi

# Create/update systemd service
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << SERVICEOF
[Unit]
Description=Geeta Pariwar CRM
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="GEETAPARIWAR_DATA_DIR=$APP_DIR/data"
Environment="SECRET_KEY=$(cat .secret_key)"
ExecStart=$APP_DIR/.venv/bin/gunicorn -w 1 -b 0.0.0.0:3201 --access-logfile - --error-logfile - wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "=== Deployment complete ==="
echo "App running at http://$(curl -s ifconfig.me):3201"
echo "Check status: sudo systemctl status $SERVICE_NAME"
