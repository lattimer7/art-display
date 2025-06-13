#!/usr/bin/env python3
"""
Fullscreen display manager for the art frame
Runs a chromium browser in kiosk mode
"""

import subprocess
import time
import os

def kill_existing_browsers():
    """Kill any existing browser instances"""
    subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
    time.sleep(1)

def start_display():
    """Start the display in fullscreen kiosk mode"""
    kill_existing_browsers()
    
    # Disable screen blanking
    subprocess.run(['xset', 's', 'off'], capture_output=True)
    subprocess.run(['xset', '-dpms'], capture_output=True)
    subprocess.run(['xset', 's', 'noblank'], capture_output=True)
    
    # Start chromium in kiosk mode
    cmd = [
        'chromium-browser',
        '--kiosk',
        '--noerrdialogs',
        '--disable-infobars',
        '--disable-session-crashed-bubble',
        '--disable-component-update',
        '--autoplay-policy=no-user-gesture-required',
        '--check-for-update-interval=31536000',
        'https://localhost/'
    ]
    
    subprocess.Popen(cmd, env={**os.environ, 'DISPLAY': ':0'})

if __name__ == "__main__":
    start_display()