#!/usr/bin/env python3
"""
Fullscreen display manager for the art frame
Runs a chromium browser in kiosk mode
"""

import subprocess
import time
import os
import sys

def kill_existing_browsers():
    """Kill any existing browser instances"""
    subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
    time.sleep(2)

def wait_for_server():
    """Wait for the web server to be ready"""
    import socket
    retries = 30
    while retries > 0:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8443))
            sock.close()
            if result == 0:
                print("Server is ready!")
                return True
        except:
            pass
        retries -= 1
        print(f"Waiting for server... ({retries} retries left)")
        time.sleep(2)
    return False

def start_display():
    """Start the display in fullscreen kiosk mode"""
    kill_existing_browsers()
    
    # Wait for server to be ready
    if not wait_for_server():
        print("Server failed to start!")
        sys.exit(1)
    
    # Disable screen blanking
    subprocess.run(['xset', 's', 'off'], capture_output=True)
    subprocess.run(['xset', '-dpms'], capture_output=True)
    subprocess.run(['xset', 's', 'noblank'], capture_output=True)
    
    # Start chromium in kiosk mode with all necessary flags
    cmd = [
        'chromium-browser',
        '--kiosk',
        '--noerrdialogs',
        '--disable-infobars',
        '--disable-session-crashed-bubble',
        '--disable-component-update',
        '--autoplay-policy=no-user-gesture-required',
        '--check-for-update-interval=31536000',
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        '--ignore-ssl-errors',
        '--allow-insecure-localhost',
        '--disable-web-security',
        '--disable-features=TranslateUI',
        '--disable-features=Translate',
        '--disable-features=ChromeWhatsNewUI',
        '--disable-gpu-sandbox',
        '--disable-software-rasterizer',
        '--disable-dev-shm-usage',
        '--disable-setuid-sandbox',
        '--no-sandbox',
        '--user-data-dir=/tmp/chromium_art_display',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        'https://localhost:8443/'
    ]
    
    # Set environment and start
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    
    subprocess.Popen(cmd, env=env)
    print("Chromium started successfully!")

if __name__ == "__main__":
    start_display()