import discord
from discord.ext import commands
from database import db  # Firestore
from .orders import Orders  # Ensure this is correctly imported

# Constants
PAID_HELP_TEST_CHANNEL = "paid-help-test"  # For testing
PAID_HELP_CHANNEL = "paid-help"  # Main channel

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Automatically send ticket embed when bot starts."""
        print("🔄 Bot has restarted. Checking for ticket system...")
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=PAID_HELP_TEST_CHANNEL)  # Use test channel
            if channel:
                await self.send_ticket_embed(channel)
                print(f"✅ Ticket embed sent in {channel.name}")
            else:
                print(f"⚠️ {PAID_HELP_TEST_CHANNEL} not found!")

    async def send_ticket_embed(self, channel):
        """Sends the ticket embed with buttons."""
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
        await channel.send(embed=embed, view=view)

    @commands.command(name="send_tickets_test")
    async def send_tickets_test(self, ctx):
        """Manually send ticket embed to #paid-help-test."""
        print("📤 Manually sending ticket embed to test channel...")
        channel = discord.utils.get(ctx.guild.text_channels, name=PAID_HELP_TEST_CHANNEL)
        if channel:
            await self.send_ticket_embed(channel)
            await ctx.send("✅ Ticket system re-sent in #paid-help-test!", delete_after=5)
        else:
            await ctx.send("⚠️ Test ticket channel not found!", delete_after=5)

    @commands.command(name="send_tickets_main")
    async def send_tickets_main(self, ctx):
        """Manually send ticket embed to #paid-help (main channel)."""
        print("📤 Manually sending ticket embed to main channel...")
        channel = discord.utils.get(ctx.guild.text_channels, name=PAID_HELP_CHANNEL)
        if channel:
            await self.send_ticket_embed(channel)
            await ctx.send("✅ Ticket system sent to #paid-help!", delete_after=5)
        else:
            await ctx.send("⚠️ Main ticket channel not found!", delete_after=5)


class TicketButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Order Here", style=discord.ButtonStyle.green)
    async def order_here(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Creates an order ticket."""
        orders_cog = self.bot.get_cog("Orders")
        await interaction.response.defer()
        if orders_cog:
            print("✅ Orders cog found, creating an order ticket...")
            await orders_cog.order(interaction)
        else:
            print("⚠️ Orders cog not found! Check if it's loaded properly.")
            await interaction.followup.send("The order system is currently unavailable.", ephemeral=True)

    @discord.ui.button(label="Sign Up to Be a Tutor", style=discord.ButtonStyle.blurple)
    async def sign_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles tutor applications."""
        tutor_cog = self.bot.get_cog("TutorSignup")
        await interaction.response.defer()
        if tutor_cog:
            print("✅ TutorSignup cog found, opening tutor application...")
            await tutor_cog.sign_up(interaction)
        else:
            print("⚠️ TutorSignup cog not found! Check if it's loaded properly.")
            await interaction.followup.send("Tutor sign-ups are not available at the moment.", ephemeral=True)

    @discord.ui.button(label="Report an Issue", style=discord.ButtonStyle.red)
    async def report_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles user reports."""
        report_cog = self.bot.get_cog("ReportSystem")
        await interaction.response.defer()
        if report_cog:
            print("✅ ReportSystem cog found, creating report ticket...")
            await report_cog.report(interaction)
        else:
            print("⚠️ ReportSystem cog not found! Check if it's loaded properly.")
            await interaction.followup.send("The report system is currently unavailable.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketSystem(bot))


       