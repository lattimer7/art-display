#!/bin/bash

# Variables for your setup
USER="blattimer"
PROJECT_DIR="/home/blattimer/code/art"
PYTHON_PATH="/home/blattimer/.pyenv/versions/art/bin/python"

echo "Setting up Raspberry Pi Art Display System..."
echo "User: $USER"
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y \
    unclutter \
    xdotool \
    nginx \
    git

# Generate self-signed SSL certificate
cd $PROJECT_DIR
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 \
    -subj "/C=US/ST=NY/L=New York/O=ArtDisplay/CN=artdisplay.local"

# Create systemd service for the app
sudo tee /etc/systemd/system/artdisplay.service > /dev/null << EOL
[Unit]
Description=Art Display Web Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PYENV_ROOT=/home/$USER/.pyenv"
Environment="PATH=/home/$USER/.pyenv/versions/art/bin:/usr/bin:/bin"
ExecStart=$PYTHON_PATH $PROJECT_DIR/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Create systemd service for the display
sudo tee /etc/systemd/system/artdisplay-screen.service > /dev/null << EOL
[Unit]
Description=Art Display Screen
After=network.target artdisplay.service

[Service]
Type=simple
User=$USER
Environment="DISPLAY=:0"
Environment="PYENV_ROOT=/home/$USER/.pyenv"
Environment="PATH=/home/$USER/.pyenv/versions/art/bin:/usr/bin:/bin"
ExecStartPre=/bin/sleep 10
ExecStart=$PYTHON_PATH $PROJECT_DIR/display.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Set up cron job for morning weather art
(crontab -l 2>/dev/null; echo "0 7 * * * cd $PROJECT_DIR && $PYTHON_PATH weather_art.py") | crontab -

# Configure auto-login and start X
sudo raspi-config nonint do_boot_behaviour B4

# Disable screen saver
echo "xset s noblank" >> ~/.xinitrc
echo "xset s off" >> ~/.xinitrc
echo "xset -dpms" >> ~/.xinitrc

# Configure mDNS
sudo apt-get install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable artdisplay.service
sudo systemctl enable artdisplay-screen.service

echo "Setup complete! Please:"
echo "1. Edit .env file with your API keys (already exists)"
echo "2. Reboot your Raspberry Pi"
echo "3. Access the control interface at https://artdisplay.local/control from your phone"