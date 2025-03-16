import discord
from discord.ext import commands
from database import db  # Firestore
from .orders import Orders  # Use a relative import for Orders
import logging

# Constants
PAID_HELP_TEST_CHANNEL = "paid-help-test"  # For testing
PAID_HELP_CHANNEL = "📚paid-help💰"  # Main channel name

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("🔄 Bot has restarted. Checking for ticket system...")
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=PAID_HELP_CHANNEL)
            if channel:
                try:
                    await self.send_ticket_embed(channel)
                    logging.info(f"✅ Ticket embed sent in {channel.name}")
                except Exception as e:
                    logging.error(f"❌ Failed to send ticket embed in {channel.name}: {e}")
            else:
                logging.warning(f"⚠️ {PAID_HELP_CHANNEL} not found in guild {guild.name}!")

    async def send_ticket_embed(self, channel):
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
        view = TicketButtons(self.bot)
        try:
            await channel.send(embed=embed, view=view)
        except Exception as e:
            logging.error(f"❌ Error sending embed to {channel.name}: {e}")
            await channel.send("⚠️ There was an error sending the ticket system embed. Please try again later.")

    @commands.command(name="send_tickets_test")
    async def send_tickets_test(self, ctx):
        logging.info("📤 Manually sending ticket embed to test channel...")
        channel = discord.utils.get(ctx.guild.text_channels, name=PAID_HELP_TEST_CHANNEL)
        if channel:
            try:
                await self.send_ticket_embed(channel)
                await ctx.send("✅ Ticket system re-sent in #paid-help-test!", delete_after=5)
            except Exception as e:
                logging.error(f"❌ Failed to send ticket embed in test channel: {e}")
                await ctx.send("⚠️ Failed to send ticket embed. Please try again later.", delete_after=5)
        else:
            await ctx.send("⚠️ Test ticket channel not found!", delete_after=5)

    @commands.command(name="send_tickets_main")
    async def send_tickets_main(self, ctx):
        logging.info("📤 Manually sending ticket embed to main channel...")
        channel = discord.utils.get(ctx.guild.text_channels, name=PAID_HELP_CHANNEL)
        if channel:
            try:
                await self.send_ticket_embed(channel)
                await ctx.send("✅ Ticket system sent to #paid-help!", delete_after=5)
            except Exception as e:
                logging.error(f"❌ Failed to send ticket embed in main channel: {e}")
                await ctx.send("⚠️ Failed to send ticket embed. Please try again later.", delete_after=5)
        else:
            await ctx.send(f"⚠️ Main ticket channel `{PAID_HELP_CHANNEL}` not found!", delete_after=5)

class TicketButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Order Here", style=discord.ButtonStyle.green)
    async def order_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            orders_cog = self.bot.get_cog("Orders")
            if orders_cog:
                logging.info("✅ Orders cog found, creating an order ticket...")
                await orders_cog.order(interaction)
            else:
                logging.warning("⚠️ Orders cog not found! Check if it's loaded properly.")
                await interaction.followup.send("The order system is currently unavailable.", ephemeral=True)
        except Exception as e:
            logging.error(f"❌ Error creating an order ticket: {e}")
            await interaction.followup.send("⚠️ An error occurred while creating your order. Please try again later.", ephemeral=True)

    @discord.ui.button(label="Sign Up to Be a Tutor", style=discord.ButtonStyle.blurple)
    async def sign_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            tutor_cog = self.bot.get_cog("TutorSignup")
            if tutor_cog:
                logging.info("✅ TutorSignup cog found, opening tutor application...")
                await tutor_cog.sign_up(interaction)
            else:
                logging.warning("⚠️ TutorSignup cog not found! Check if it's loaded properly.")
                await interaction.followup.send("Tutor sign-ups are not available at the moment.", ephemeral=True)
        except Exception as e:
            logging.error(f"❌ Error handling tutor sign-up: {e}")
            await interaction.followup.send("⚠️ An error occurred during the tutor sign-up process. Please try again later.", ephemeral=True)

    @discord.ui.button(label="Report an Issue", style=discord.ButtonStyle.red)
    async def report_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            report_cog = self.bot.get_cog("ReportSystem")
            if report_cog:
                logging.info("✅ ReportSystem cog found, creating report ticket...")
                await report_cog.report(interaction)
            else:
                logging.warning("⚠️ ReportSystem cog not found! Check if it's loaded properly.")
                await interaction.followup.send("The report system is currently unavailable.", ephemeral=True)
        except Exception as e:
            logging.error(f"❌ Error creating a report ticket: {e}")
            await interaction.followup.send("⚠️ An error occurred while reporting the issue. Please try again later.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))



