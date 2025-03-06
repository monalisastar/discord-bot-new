import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get values from .env
BOT_PREFIX = "!"  # Set your bot's prefix
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FIREBASE_CREDENTIALS = "serviceAccount.json"  # Path to Firebase JSON file