import discord
from discord.ext import commands
from database import db  # Firestore
from .orders import Orders  # ✅ Ensure this is correctly imported

# Constants
PAID_HELP_TEST_CHANNEL = "paid-help-test"  # For testing
PAID_HELP_CHANNEL = "paid-help"  # Main channel

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Automatically send ticket embed when bot starts."""
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=PAID_HELP_TEST_CHANNEL)  # Use test channel
            if channel:
                await self.send_ticket_embed(channel)
                print(f"✅ Ticket embed sent in {channel.name}")
            else:
                print(f"❌ {PAID_HELP_TEST_CHANNEL} not found!")

    async def send_ticket_embed(self, channel):
        """Sends the ticket embed with the welcome message and buttons."""
        embed = discord.Embed(
            title="📚 HIRE A TUTOR",
            description=(
                "Welcome to the official **Hire A Tutor** community! 🎓\n"
                "Here you will find the best tutors to assist you with your tasks!\n\n"
                "📌 **THIS IS A PAID SERVICE ONLY**\n"
                "📌 **Deal with** __Professional Tutors__.\n"
                "📌 **Get help in** __any subject__.\n"
                "📌 **100% satisfaction guaranteed.**\n"
                "📌 **1-on-1 relationships you can** __trust__.\n"
                "📌 **Quick turnaround time.**\n"
                "📌 **On-demand tutoring.**\n\n"
                "🛡️ **A full refund is guaranteed if any issue is found.**\n"
                "📌 **We'll create a private channel and our bot will find you a tutor!**\n\n"
            ),
            color=discord.Color.green()
        )

        view = TicketButtons(self.bot)
        await channel.send(embed=embed, view=view)

class TicketButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="📌 Order Here", style=discord.ButtonStyle.green)
    async def order_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Creates an order ticket."""
        orders_cog = self.bot.get_cog("Orders")
        if orders_cog:
            await interaction.response.send_message("✅ Creating your order ticket...", ephemeral=True)
            await orders_cog.order(interaction)  # Ensure this method exists
        else:
            await interaction.response.send_message("❌ Order system is currently unavailable.", ephemeral=True)

    @discord.ui.button(label="✍️ Sign Up to Be a Tutor", style=discord.ButtonStyle.blurple)
    async def sign_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles tutor applications."""
        tutor_cog = self.bot.get_cog("TutorSignup")
        if tutor_cog:
            await interaction.response.send_message("✅ Opening tutor application...", ephemeral=True)
            await tutor_cog.sign_up(interaction)
        else:
            await interaction.response.send_message("🚀 Tutor sign-ups are not available at the moment.", ephemeral=True)

    @discord.ui.button(label="⚠️ Report an Issue", style=discord.ButtonStyle.red)
    async def report_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles user reports."""
        report_cog = self.bot.get_cog("ReportSystem")
        if report_cog:
            await interaction.response.send_message("✅ Opening a report ticket...", ephemeral=True)
            await report_cog.report(interaction)
        else:
            await interaction.response.send_message("🔍 Report system is currently unavailable.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
