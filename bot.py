import os
from dotenv import load_dotenv  # Added to load .env variables
load_dotenv()  # Load environment variables from .env

import discord
from discord.ext import commands, tasks
from config import BOT_PREFIX  # Only import the bot prefix
import firebase_admin
from firebase_admin import credentials
import logging
import signal
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
print("DEBUG: TOKEN loaded is:", TOKEN)  # Temporary debug print (remove after confirming)

# Initialize Firebase only if it's not already initialized
if not firebase_admin._apps:
    try:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            logging.error("❌ serviceAccount.json not found. Ensure it's uploaded or set in environment variables.")
            exit(1)  # Exit the script if Firebase credentials are missing
    except Exception as e:
        logging.error(f"❌ Firebase initialization failed: {e}")
        exit(1)

# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure message content access

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# List of cogs (modules) - Ensure 'cogs.orders' loads before 'cogs.tutor_matching'
COGS = [
    "cogs.tickets",
    "cogs.orders",
    "cogs.tutor_signup",
    "cogs.report",
    "cogs.payments",
    "cogs.tutor_matching"
]

# Graceful shutdown for SIGTERM and SIGINT (e.g., when manually stopping or restarting)
def handle_shutdown(signal, frame):
    logging.info("Bot is shutting down gracefully...")
    bot.loop.create_task(bot.close())

signal.signal(signal.SIGINT, handle_shutdown)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown)  # System shutdown

@bot.event
async def on_ready():
    logging.info(f"✅ Logged in as {bot.user}")

    # Load all cogs asynchronously
    for cog in COGS:
        try:
            await bot.load_extension(cog)  # Ensure proper async loading
            logging.info(f"✅ Loaded {cog}")
        except Exception as e:
            logging.error(f"❌ Failed to load {cog}: {e}")

    # Debug: Print out the loaded cogs to verify they are registered correctly
    logging.info(f"🔍 Currently loaded cogs: {list(bot.cogs.keys())}")

    # Ensure bot is in a server
    if not bot.guilds:
        logging.error("❌ Bot is not connected to any server!")
        return

    # Auto-send ticket embed in #paid-help-test (if needed)
    guild = bot.guilds[0]  # Get the first server the bot is in
    channel = discord.utils.get(guild.text_channels, name="paid-help-test")

    if channel:
        tickets_cog = bot.get_cog("TicketSystem")
        if tickets_cog:
            try:
                await tickets_cog.send_ticket_embed(channel)
            except Exception as e:
                logging.error(f"❌ Failed to send ticket embed: {e}")
        else:
            logging.error("❌ TicketSystem cog not loaded!")
    else:
        logging.error("❌ #paid-help-test channel not found!")

# Global error handler for commands
@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Error occurred in command '{ctx.command}': {str(error)}")
    
    # Handle specific error types
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("⚠️ Command not found! Please check the available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing arguments. Please provide the required input.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("⚠️ I don't have permission to perform that action!")
    else:
        await ctx.send("⚠️ An unexpected error occurred. Please try again later.")

# Global error handler for uncaught exceptions in events
@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"An error occurred in event: {event}")
    logging.exception("Exception traceback:")

# Periodic health check (heartbeat) to ensure the bot stays online
@tasks.loop(minutes=5)  # Runs every 5 minutes to check the bot's health
async def health_check():
    try:
        # Check if the bot is responding to a simple ping
        logging.info("Performing health check...")
        await bot.get_channel(1234567890).send("🟢 Bot is alive and running!")  # Replace with your own channel ID
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        # Optionally, notify admins if health check fails
        admin_channel = bot.get_channel(1234567890)  # Replace with your admin channel ID
        if admin_channel:
            await admin_channel.send(f"⚠️ Health check failed: {e}")

# Running the bot
async def main():
    try:
        async with bot:
            await bot.start(TOKEN)
    except Exception as e:
        logging.error(f"❌ Error starting the bot: {e}")

if TOKEN:
    import asyncio
    asyncio.run(main())
else:
    logging.error("❌ DISCORD_BOT_TOKEN is not set! Check your environment variables.")





