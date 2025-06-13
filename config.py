import os
from datetime import datetime

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'your-weather-api-key')

# NYC Coordinates
NYC_LAT = 40.7128
NYC_LON = -74.0060

# Display settings
DISPLAY_WIDTH = 1920
DISPLAY_HEIGHT = 1080
IMAGE_GENERATION_SIZE = "1536x1024"  # OpenAI supports 1024x1024, 1792x1024, or 1024x1792

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
CURRENT_IMAGE = os.path.join(IMAGES_DIR, 'current.png')

# Server settings
HOST = '0.0.0.0'
PORT = 443
DEBUG = False

# Art generation settings
MORNING_GENERATION_TIME = "07:00"  # 7 AM
DEFAULT_STYLE = "ethereal digital art, cinematic lighting, highly detailed"
PARTIAL_IMAGES = 3  # Number of partial images to receive during streaming (1-10)