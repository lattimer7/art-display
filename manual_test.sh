#!/bin/bash

# Manual Test Script for Art Display
echo "=== Manual Test Script ==="

PROJECT_DIR="/home/blattimer/code/art-display"
PYTHON_PATH="/home/blattimer/.pyenv/versions/art/bin/python"

cd $PROJECT_DIR

echo "1. Testing Python and dependencies..."
$PYTHON_PATH -c "
import flask
import flask_socketio
import openai
import requests
from dotenv import load_dotenv
print('✓ All Python imports successful')
"

echo ""
echo "2. Testing environment variables..."
$PYTHON_PATH -c "
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY', 'not-set')
print(f'OPENAI_API_KEY: {"SET" if api_key != "not-set" and api_key != "your-openai-api-key-here" else "NOT SET"}')
weather_key = os.getenv('OPENWEATHER_API_KEY', 'not-set')
print(f'OPENWEATHER_API_KEY: {"SET" if weather_key != "not-set" and weather_key != "your-weather-api-key-here" else "NOT SET"}')
"

echo ""
echo "3. Testing certificates..."
if [ -f certs/cert.pem ] && [ -f certs/key.pem ]; then
    echo "✓ SSL certificates exist"
    openssl x509 -in certs/cert.pem -text -noout | grep "Subject:"
else
    echo "✗ SSL certificates missing!"
fi

echo ""
echo "4. Starting web server in foreground..."
echo "Press Ctrl+C to stop"
echo "You should see the server start on https://0.0.0.0:8443"
echo ""
$PYTHON_PATH app.py