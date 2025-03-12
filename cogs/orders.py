import discord
from discord.ext import commands
import asyncio
import re  # For currency validation
from database import db  # Firestore Database

# Constants
TRUSTED_TUTOR_ROLE = "Trusted tutor"
TUTOR_CHAT_CHANNEL = "tutor-chat"
TICKET_CATEGORY_ID = 1346355213358862397 # Update this to match your category ID

class FindTutorView(discord.ui.View):
    """View with a 'Find Tutor' button."""
    def __init__(self, ticket_channel, user, responses):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.user = user
        self.responses = responses

    @discord.ui.button(label="Find Tutor", style=discord.ButtonStyle.green)
    async def find_tutor(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles 'Find Tutor' button click."""
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Only the ticket owner can use this.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Searching for a tutor...", ephemeral=True)

        guild = interaction.guild
        tutor_role = discord.utils.get(guild.roles, name=TRUSTED_TUTOR_ROLE)
        tutor_chat = discord.utils.get(guild.text_channels, name=TUTOR_CHAT_CHANNEL)

        if not tutor_role or not tutor_chat:
            await self.ticket_channel.send("❌ Error: No Trusted Tutors or tutor-chat found.")
            return

        embed = discord.Embed(
            title="📌 New Order Alert!",
            description=(
                f"🔹 **Client:** {self.user.mention}\n"
                f"🔹 **Category:** {self.responses['category']}\n"
                f"🔹 **Field:** {self.responses['field']}\n"
                f"🔹 **Due Date:** {self.responses['due_date']}\n"
                f"🔹 **Budget:** {self.responses['budget']}\n"
                "📩 Click 'Claim' to take this order."
            ),
            color=discord.Color.gold()
        )

        view = ClaimRejectView(self.ticket_channel, self.user)# Notify tutors
        await tutor_chat.send(tutor_role.mention, embed=embed, view=view)
        for tutor in guild.members:
            if tutor_role in tutor.roles:
                try:
                    await tutor.send(embed=embed, view=view)
                except:
                    pass  # Ignore failed DMs

        await self.ticket_channel.send("✅ Tutors have been notified!")

class ClaimRejectView(discord.ui.View):
    """View with 'Claim' and 'Reject' buttons."""
    def __init__(self, ticket_channel, user):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.user = user

    @discord.ui.button(label="✅ Claim", style=discord.ButtonStyle.green)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the claim button."""
        tutor = interaction.user
        guild = interaction.guild

        # Grant tutor access
        await self.ticket_channel.set_permissions(tutor, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ {tutor.mention} has claimed this ticket!", ephemeral=True)
        await self.ticket_channel.send(f"🎉 {tutor.mention} has claimed your ticket, {self.user.mention}!")

        # Disable claim button
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "✅ Claim":
                child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the reject button."""
        await interaction.response.send_message("❌ Ticket rejected.", ephemeral=True)

class Orders(commands.Cog):
    """Handles order ticket creation and tutor assignment."""
    def __init__(self, bot):
        self.bot = bot

    def generate_ticket_name(self, user):
        """Generate a unique ticket name."""
        tickets_ref = db.collection("tickets")
        ticket_count = len(tickets_ref.get()) + 1
        return f"{user.name}{ticket_count}"

    async def order(self, interaction: discord.Interaction):
        """Creates an order ticket."""
        user = interaction.user
        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)

        if not category:
            await interaction.response.send_message("❌ Ticket category not found!", ephemeral=True)
            return

        # Create ticket channel
        ticket_channel = await guild.create_text_channel(
            name=self.generate_ticket_name(user),
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )

        await ticket_channel.send(f"Hi {user.mention}, let's get started with your order!")

        responses = await self.ask_questions(ticket_channel, user)  
        if responses is None:
            await ticket_channel.delete()
            return

        # Show 'Find Tutor' button
        view = FindTutorView(ticket_channel, user, responses)
        await ticket_channel.send("✅ Click below to find a tutor:", view=view)

    async def ask_questions(self, channel, user):
        """Asks interactive questions and collects responses."""
        def check(m):
            return m.author == user and m.channel == channel

        questions = [
            ("📌 How can we help you today? (Assignment, Quiz, Exam, Essay)", "category"),
            ("📚 What is your field of study and level?", "field"),
            ("⏳ When is it due?", "due_date"),
            ("💰 What’s your budget?", "budget"),
            ("📂 Any additional details?", "extra_info")
        ]

        responses = {}

        for question, key in questions:
            await channel.send(question)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=120)
                if key == "budget":
                    budget_value, currency_symbol = self.parse_budget(msg.content)
                    if budget_value < 20:
                        await channel.send("⚠️ Minimum budget is $20.")
                    responses[key] = f"{currency_symbol}{budget_value}"
                else:
                    responses[key] = msg.content
            except asyncio.TimeoutError:
                await channel.send("⏳ Timeout. Ticket creation cancelled.")
                return None

        return responses

    def parse_budget(self, budget_input):
        """Extracts budget amount and currency from input."""
        match = re.search(r"([$£€₹¥₩C$])?(\d+(\.\d{1,2})?)", budget_input.strip())
        if not match:
            return None, None
        return float(match.group(2)), match.group(1) if match.group(1) else "$"

async def setup(bot):
    await bot.add_cog(Orders(bot))