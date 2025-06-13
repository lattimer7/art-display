#!/bin/bash

# Debug script for Art Display
echo "=== Art Display Debug Script ==="

PROJECT_DIR="/home/blattimer/code/art-display"
cd $PROJECT_DIR

echo "1. Checking directory structure..."
echo "Current directory: $(pwd)"
echo ""
echo "Project files:"
ls -la
echo ""

echo "2. Checking images directory..."
if [ -d "images" ]; then
    echo "Images directory exists:"
    ls -la images/
else
    echo "ERROR: Images directory missing!"
    echo "Creating images directory..."
    mkdir -p images
fi
echo ""

echo "3. Checking for current.png..."
if [ -f "images/current.png" ]; then
    echo "✓ current.png exists"
    echo "File details:"
    ls -la images/current.png
else
    echo "✗ current.png missing!"
    echo "Creating placeholder image..."
    
    # Create a simple black image using Python
    /home/blattimer/.pyenv/versions/art/bin/python -c "
import os
os.makedirs('images', exist_ok=True)

# Create a black placeholder image
with open('images/current.png', 'wb') as f:
    # PNG header and minimal black image data
    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00IEND\xaeB`\x82')
print('Created minimal placeholder image')
"
fi
echo ""

echo "4. Testing image endpoint..."
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/current-image
echo " (HTTP response code)"
echo ""

echo "5. Checking Python app configuration..."
/home/blattimer/.pyenv/versions/art/bin/python -c "
import config
import os
print(f'IMAGES_DIR: {config.IMAGES_DIR}')
print(f'CURRENT_IMAGE: {config.CURRENT_IMAGE}')
print(f'File exists: {os.path.exists(config.CURRENT_IMAGE)}')
print(f'Working directory: {os.getcwd()}')
"
echo ""

echo "6. Checking service logs for errors..."
echo "Recent app errors:"
sudo journalctl -u artdisplay.service -n 20 --no-pager | grep -E "(ERROR|Error|error|Exception|Traceback)"
echo ""

echo "7. Testing app routes..."
echo "Testing root endpoint:"
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/
echo " - / endpoint"

echo "Testing control endpoint:"
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/control
echo " - /control endpoint"

echo "Testing current-image endpoint:"
curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/current-image
echo " - /current-image endpoint"
echo ""

echo "8. File permissions check..."
echo "Images directory permissions:"
ls -ld images/
echo "Current user: $(whoami)"
echo "App service user: blattimer"

echo ""
echo "=== Debug Summary ==="
echo "If you see 404 errors above, run this fix:"
echo "cd $PROJECT_DIR && mkdir -p images && touch images/current.png"
echo ""
echo "To restart services after fixing:"
echo "sudo systemctl restart artdisplay.service"
echo "sudo systemctl restart artdisplay-screen.service"