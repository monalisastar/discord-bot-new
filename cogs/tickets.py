import discord
from discord.ext import commands
from database import db  # Firestore
from .orders import Orders  # Ensure this is correctly imported

# Constants
PAID_HELP_TEST_CHANNEL = "paid-help-test"  # For testing
PAID_HELP_CHANNEL = "paid-help"  # Main channel

class TicketSystem(commands.Cog):
    def __init__(self, bot):  # ✅ Fixed __init__ method
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
                print(f"⚠️ {PAID_HELP_TEST_CHANNEL} not found!")

    async def send_ticket_embed(self, channel):
        """Sends the ticket embed with the welcome message and buttons."""
        embed = discord.Embed(
            title="HIRE A TUTOR",
            description=(
                "Welcome to the official Hire A Tutor community! \n"
                "Here you will find the best tutors to assist you with your tasks!\n\n"
                "**THIS IS A PAID SERVICE ONLY**\n"
                "✔️ Deal with Professional Tutors.\n"
                "✔️ Get help in any subject.\n"
                "✔️ 100% satisfaction guaranteed.\n"
                "✔️ 1-on-1 relationships you can trust.\n"
                "✔️ Quick turnaround time.\n"
                "✔️ On-demand tutoring.\n\n"
                "**A full refund is guaranteed if any issue is found.**\n"
                "We'll create a private channel and our bot will find you a tutor!\n\n"
            ),
            color=discord.Color.green()
        )

        view = TicketButtons(self.bot)  # ✅ No indentation issue
        await channel.send(embed=embed, view=view)  # ✅ Proper indentation

class TicketButtons(discord.ui.View):  # ✅ Ensure no extra space before class
    def _init(self, bot):  # ✅ Fixed __init_ method
        super()._init_()  # ✅ Corrected super() call
        self.bot = bot

    @discord.ui.button(label="Order Here", style=discord.ButtonStyle.green)
    async def order_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Creates an order ticket."""
        orders_cog = self.bot.get_cog("Orders")
        if orders_cog:
            await interaction.response.defer()  # Prevents "Interaction Failed"
            print(" Orders cog found, creating your order ticket...")
            await orders_cog.order(interaction)
        else:
            print(" Orders cog not found! Check if cogs.orders is loaded properly.")
            await interaction.response.send_message("The order system is currently unavailable.", ephemeral=True)

    @discord.ui.button(label="Sign Up to Be a Tutor", style=discord.ButtonStyle.blurple)
    async def sign_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles tutor applications."""
        tutor_cog = self.bot.get_cog("TutorSignup")
        if tutor_cog:
            await interaction.response.defer()  # Prevents "Interaction Failed"
            print(" TutorSignup cog found, opening the tutor application ticket...")
            await tutor_cog.sign_up(interaction)
        else:
            print(" TutorSignup cog not found! Check if cogs.tutor_signup is loaded properly.")
            await interaction.response.send_message("Tutor sign-ups are not available at the moment.", ephemeral=True)

    @discord.ui.button(label="Report an Issue", style=discord.ButtonStyle.red)
    async def report_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles user reports."""
        report_cog = self.bot.get_cog("ReportSystem")
        if report_cog:
            await interaction.response.defer()  # Prevents "Interaction Failed"
            print(" ReportSystem cog found, creating your report ticket...")
            await report_cog.report(interaction)
        else:
            print(" ReportSystem cog not found! Check if cogs.report is loaded properly.")
            await interaction.response.send_message("The report system is currently unavailable.", ephemeral=True)

#Ensure this is on a new line
async def setup(bot):
    await bot.add_cog(TicketSystem(bot))

       