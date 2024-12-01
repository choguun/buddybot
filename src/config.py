import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base triggers and partial triggers
TRIGGER_PHRASES = ["hey omi", "hey, omi"]
PARTIAL_FIRST = ["hey", "hey,"]
PARTIAL_SECOND = ["omi"]

# Timing configurations
QUESTION_AGGREGATION_TIME = 5  # seconds
NOTIFICATION_COOLDOWN = 10  # seconds
CLEANUP_INTERVAL = 300  # 5 minutes
SESSION_EXPIRY = 3600  # 1 hour

# OpenAI configurations
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = "gpt-4"
MAX_TOKENS = 150
TEMPERATURE = 0.7
TIMEOUT = 30

# OpenWeatherMap configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Flask configurations
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('FLASK_ENV') == 'development' 