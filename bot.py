import os
import discord
from discord.ext import commands
from config import BOT_PREFIX  # Only import the bot prefix

# Get the bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure message content access

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# List of cogs (modules)
COGS = ["cogs.tickets", "cogs.orders", "cogs.tutor_signup", "cogs.report", "cogs.payments"]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
# Load all cogs
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

    # Send ticket embed in #paid-help-test
    guild = bot.guilds[0] if bot.guilds else None  # Ensure the bot is in a server
    if guild:
        channel = discord.utils.get(guild.text_channels, name="paid-help-test")
        if channel:
            tickets_cog = bot.get_cog("TicketSystem")
            if tickets_cog:
                await tickets_cog.send_ticket_embed(channel)
            else:
                print("❌ TicketSystem cog not loaded!")
        else:
            print("❌ #paid-help-test channel not found!")
    else:
        print("❌ Bot is not connected to any server!")

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_BOT_TOKEN is not set! Check your environment variables.")