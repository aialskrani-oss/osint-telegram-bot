"""
PythonAnywhere WSGI configuration file.
Paste the contents of this file into your PythonAnywhere WSGI config
(found at: Web tab → WSGI configuration file).

Replace 'YOUR_USERNAME' with your PythonAnywhere username.
"""
import sys
import os

# Add your project directory to Python path
project_home = '/home/YOUR_USERNAME/osint-telegram-bot'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = 'YOUR_TOKEN_HERE'
os.environ['WEBHOOK_SECRET'] = 'osint_secure_path'
os.environ['DB_PATH'] = f'{project_home}/osint_bot.db'

# Import the Flask app
from bot_webhook import flask_app as application
