import discord
from discord.ext import commands
from database import db  # Firestore

# Category where report tickets will be created
REPORT_CATEGORY = "User Reports"

class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function to generate report ticket name
    def generate_ticket_name(self, user):
        reports_ref = db.collection("reports")
        report_count = len(reports_ref.get()) + 1
        return f"report-{user.name}{report_count}"

    # Function to ask report questions
    async def ask_report_questions(self, channel, user):
        def check(m):
            return m.author == user and m.channel == channel

        questions = [
            ("Who are you reporting? (Username or ID)", "reported_user"),
            ("What is the issue? (Describe in detail)", "issue_description"),
            ("Do you have any proof? (Attach files or provide links)", "evidence"),
        ]

        responses = {}

        for question, key in questions:
            await channel.send(question)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=120)

                # Check if user uploads a file
                if msg.attachments:
                    responses[key] = msg.attachments[0].url  # Store file URL
                else:
                    responses[key] = msg.content

            except TimeoutError:
                await channel.send("You took too long to respond. Report cancelled.")
                return None

        return responses

    # Report button interaction
    class ReportButton(discord.ui.View):
        def __init__(self, bot, user):
            super().__init__()
            self.bot = bot
            self.user = user

        @discord.ui.button(label="Report an Issue", style=discord.ButtonStyle.danger)
        async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name=REPORT_CATEGORY)

            if not category:
                category = await guild.create_category(REPORT_CATEGORY)

            # Create a private report ticket
            ticket_name = f"report-{self.user.name}{len(db.collection('reports').get()) + 1}"
            ticket_channel = await guild.create_text_channel(ticket_name, category=category)

            # Set permissions for user
            await ticket_channel.set_permissions(self.user, read_messages=True, send_messages=True)

            await ticket_channel.send(f"Hi {self.user.mention}, welcome to the report system. Please answer the following questions.")

            # Ask questions
            responses = await ReportSystem.ask_report_questions(self.bot, ticket_channel, self.user)

            if responses:
                # Store report in Firestore
                report_data = {
                    "user_id": self.user.id,
                    "username": self.user.name,
                    "reported_user": responses["reported_user"],
                    "issue_description": responses["issue_description"],
                    "evidence": responses["evidence"],
                    "status": "pending"
                }
                db.collection("reports").document().set(report_data)

                await ticket_channel.send(f"Thank you for reporting, {self.user.mention}. Our team will review your report and take appropriate action.")

# Setup function for cog
async def setup(bot):
    await bot.add_cog(ReportSystem(bot))
