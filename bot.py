import os
import discord
from discord.ext import commands
from config import BOT_PREFIX, TOKEN  # Load bot prefix and token from config.py

# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure message content access

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Load cogs (modules)
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
    guild = bot.guilds[0]  # Assuming the bot is in one server
    channel = discord.utils.get(guild.text_channels, name="paid-help-test")

    if channel:
        tickets_cog = bot.get_cog("TicketSystem")
        if tickets_cog:
            await tickets_cog.send_ticket_embed(channel)
        else:
            print("❌ TicketSystem cog not loaded!")
    else:
        print("❌ #paid-help-test channel not found!")

# Run the bot
bot.run(TOKEN)