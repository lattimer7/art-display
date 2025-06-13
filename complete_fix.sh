#!/bin/bash

# Complete Fix Script for Art Display System
echo "=== Art Display Complete Fix Script ==="

# CORRECT Variables
USER="blattimer"
PROJECT_DIR="/home/blattimer/code/art-display"  # FIXED PATH
PYTHON_PATH="/home/blattimer/.pyenv/versions/art/bin/python"

echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"

# Stop all services first
echo "Stopping services..."
sudo systemctl stop artdisplay.service 2>/dev/null
sudo systemctl stop artdisplay-screen.service 2>/dev/null
sudo systemctl disable artdisplay.service 2>/dev/null
sudo systemctl disable artdisplay-screen.service 2>/dev/null

# Kill any hanging processes
pkill -f chromium
pkill -f "python.*app.py"
pkill -f "python.*display.py"
sleep 2

# Change to project directory
cd $PROJECT_DIR || {
    echo "ERROR: Project directory not found at $PROJECT_DIR"
    echo "Please ensure your code is in /home/blattimer/code/art-display/"
    exit 1
}

# Create necessary directories
echo "Creating directories..."
mkdir -p images
mkdir -p certs
mkdir -p templates
mkdir -p static

# Create a placeholder image
echo "Creating placeholder image..."
if command -v convert &> /dev/null; then
    convert -size 1920x1080 xc:black -fill white -gravity center \
        -pointsize 72 -annotate +0+0 'Art Display Ready' \
        images/current.png
else
    # Create a simple black image using Python if ImageMagick not installed
    $PYTHON_PATH -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1920, 1080), color='black')
img.save('images/current.png')
print('Created placeholder image')
" 2>/dev/null || echo "Note: Install python-imaging or imagemagick for better placeholder"
fi

# Install/Update Python dependencies
echo "Installing Python dependencies..."
$PYTHON_PATH -m pip install --upgrade pip
$PYTHON_PATH -m pip install python-dotenv  # Make sure dotenv is installed
$PYTHON_PATH -m pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
OPENAI_API_KEY=your-openai-api-key-here
OPENWEATHER_API_KEY=your-weather-api-key-here
EOL
    echo "WARNING: Please edit .env file with your actual API keys!"
fi

# Generate new SSL certificates
echo "Generating SSL certificates..."
rm -rf certs/*
openssl req -x509 -newkey rsa:4096 -nodes \
    -out certs/cert.pem \
    -keyout certs/key.pem \
    -days 365 \
    -subj "/C=US/ST=NY/L=New York/O=ArtDisplay/CN=localhost" \
    2>/dev/null

# Create the CORRECTED systemd service files
echo "Creating systemd service files..."

sudo tee /etc/systemd/system/artdisplay.service > /dev/null << EOL
[Unit]
Description=Art Display Web Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PYENV_ROOT=/home/$USER/.pyenv"
Environment="PATH=/home/$USER/.pyenv/versions/art/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=$PROJECT_DIR"
ExecStartPre=/bin/sleep 5
ExecStart=$PYTHON_PATH $PROJECT_DIR/app.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

sudo tee /etc/systemd/system/artdisplay-screen.service > /dev/null << EOL
[Unit]
Description=Art Display Screen
After=network-online.target artdisplay.service
Wants=network-online.target
Requires=artdisplay.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/$USER/.Xauthority"
Environment="PYENV_ROOT=/home/$USER/.pyenv"
Environment="PATH=/home/$USER/.pyenv/versions/art/bin:/usr/local/bin:/usr/bin:/bin"
ExecStartPre=/bin/sleep 20
ExecStart=$PYTHON_PATH $PROJECT_DIR/display.py
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
sudo systemctl daemon-reload

# Set executable permissions
chmod +x app.py
chmod +x display.py
chmod +x weather_art.py

# Test the app first
echo "Testing web app..."
timeout 10 $PYTHON_PATH app.py > /tmp/app_test.log 2>&1 &
APP_PID=$!
sleep 5

if ps -p $APP_PID > /dev/null; then
    echo "✓ App started successfully!"
    # Test HTTPS connection
    if curl -k https://localhost:8443/ > /dev/null 2>&1; then
        echo "✓ HTTPS server responding!"
    else
        echo "✗ HTTPS server not responding. Check /tmp/app_test.log"
    fi
    kill $APP_PID 2>/dev/null
else
    echo "✗ App failed to start. Errors:"
    cat /tmp/app_test.log
    echo ""
    echo "Attempting to fix common issues..."
    
    # Try to fix permission on Python for port binding
    sudo setcap 'cap_net_bind_service=+ep' $PYTHON_PATH 2>/dev/null
fi

# Enable and start services
echo "Starting services..."
sudo systemctl enable artdisplay.service
sudo systemctl enable artdisplay-screen.service
sudo systemctl start artdisplay.service

# Wait for web service to start
echo "Waiting for web service to start..."
sleep 10

# Check web service status
if sudo systemctl is-active --quiet artdisplay.service; then
    echo "✓ Web service is running!"
    sudo systemctl start artdisplay-screen.service
    echo "✓ Display service started!"
else
    echo "✗ Web service failed to start!"
    echo "Checking logs..."
    sudo journalctl -u artdisplay.service -n 20 --no-pager
fi

# Final status check
echo ""
echo "=== Final Status ==="
echo "Web Service:"
sudo systemctl status artdisplay.service --no-pager | head -n 5
echo ""
echo "Display Service:"
sudo systemctl status artdisplay-screen.service --no-pager | head -n 5

echo ""
echo "=== Setup Complete! ==="
echo "1. Edit .env file with your actual API keys"
echo "2. Monitor logs: sudo journalctl -u artdisplay.service -f"
echo "3. Access control: https://artdisplay.local:8443/control (or use IP address)"
echo ""
echo "If display still has issues, try:"
echo "  - Reboot the Pi: sudo reboot"
echo "  - Test manually: DISPLAY=:0 chromium-browser --kiosk --ignore-certificate-errors https://localhost:8443/"
echo ""
echo "To check for errors:"
echo "  - Web service: sudo journalctl -u artdisplay.service -n 50"
echo "  - Display: sudo journalctl -u artdisplay-screen.service -n 50"