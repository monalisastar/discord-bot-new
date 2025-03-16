
import discord
from discord.ext import commands
import asyncio
from database import db  # Firestore Database for Order Storage

# Constants
TRUSTED_TUTOR_ROLE = "Trusted tutor"

TUTOR_CHAT_CHANNEL_ID = 1295087215524712518  # Tutor-Chat Channel ID

class TutorMatching(commands.Cog):
    """Handles tutor matching when 'Find Tutor' is pressed."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(">>> TutorMatching cog has been constructed!")

    async def match_tutor(self, ticket_channel: discord.TextChannel, user: discord.User):
        """Finds a tutor and assigns them the order."""
        guild = ticket_channel.guild
        
        # Ensure the "Trusted tutor" role exists
        tutor_role = discord.utils.get(guild.roles, name=TRUSTED_TUTOR_ROLE)
        if not tutor_role:
            await ticket_channel.send("⚠️ No tutor with the 'Trusted tutor' role found!")
            return
        
        tutor_chat = guild.get_channel(TUTOR_CHAT_CHANNEL_ID)
        tutors = [member for member in guild.members if tutor_role in member.roles]

        # Fetch order details from the database
        order_ref = db.collection("orders").document(str(user.id))
        try:
            order_snapshot = order_ref.get()
            order_data = order_snapshot.to_dict() if order_snapshot.exists else {}
        except Exception as e:
            await ticket_channel.send(f"⚠️ Error fetching order details: {str(e)}")
            return
        
        order_summary = (
            f"**Help Request:** {order_data.get('help_request', 'N/A')}\n"
            f"**Subject:** {order_data.get('subject', 'N/A')}\n"
            f"**Budget:** {order_data.get('budget', 'N/A')}"
        )

        # Embed for tutors
        embed = discord.Embed(
            title="📌 New Order Alert!",
            description=(
                f"🔹 **Client:** {user.mention}\n\n"
                f"**Order Summary:**\n{order_summary}\n\n"
                "📩 Click 'Claim' to take this order."
            ),
            color=discord.Color.gold()
        )
        view = ClaimRejectView(ticket_channel, user)

        # Notify tutors via tutor-chat (insulated from crashing)
        if tutor_chat:
            try:
                await tutor_chat.send(tutor_role.mention, embed=embed, view=view)
            except Exception as e:
                await ticket_channel.send(f"⚠️ Error notifying tutors in tutor-chat: {str(e)}")

        for tutor in tutors:
            try:
                await tutor.send(embed=embed, view=view)
            except Exception:
                pass

        await ticket_channel.send("✅ Tutors have been notified!")

class ClaimRejectView(discord.ui.View):
    """View with 'Claim' and 'Reject' buttons for tutors."""
    def __init__(self, ticket_channel: discord.TextChannel, user: discord.User):
        super().__init__(timeout=None)  # No timeout here as per your preference
        self.ticket_channel = ticket_channel
        self.user = user

    @discord.ui.button(label="✅ Claim", style=discord.ButtonStyle.green)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tutor claims the ticket."""
        tutor = interaction.user

        # Ensure the tutor only claims the ticket once
        permissions = self.ticket_channel.permissions_for(tutor)
        if not permissions.read_messages:
            await self.ticket_channel.set_permissions(tutor, read_messages=True, send_messages=True)

        await interaction.response.send_message(f"✅ You have claimed this ticket!", ephemeral=True)
        await self.ticket_channel.send(f"🎉 {tutor.mention} has claimed the ticket for {self.user.mention}!")

        # Attach tutor-only buttons
        view = OrderProgressView(self.ticket_channel, self.user, tutor)
        await self.ticket_channel.send("🔄 Update order status:", view=view)

        button.disabled = True
        await interaction.message.edit(view=self)

class OrderProgressView(discord.ui.View):
    """Tutor-only view for marking 'Work in Progress' or 'Order Submitted'."""
    def __init__(self, ticket_channel: discord.TextChannel, user: discord.User, tutor: discord.Member):
        super().__init__(timeout=900)  # Timeout after 15 minutes
        self.ticket_channel = ticket_channel
        self.user = user
        self.tutor = tutor

    @discord.ui.button(label="🛠 Work in Progress", style=discord.ButtonStyle.blurple)
    async def work_in_progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tutor marks the order as in progress."""
        if interaction.user != self.tutor:
            return await interaction.response.send_message("❌ Only the assigned tutor can update this!", ephemeral=True)

        await interaction.response.send_message("🛠 You marked the order as in progress.", ephemeral=True)
        await self.ticket_channel.send(f"🛠 {self.tutor.mention} is now working on the order for {self.user.mention}!")

        button.disabled = True
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "📩 Order Submitted":
                child.disabled = False

        await interaction.message.edit(view=self)

    @discord.ui.button(label="📩 Order Submitted", style=discord.ButtonStyle.green, disabled=True)
    async def order_submitted(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tutor marks the order as submitted."""
        if interaction.user != self.tutor:
            return await interaction.response.send_message("❌ Only the assigned tutor can submit the order!", ephemeral=True)

        await interaction.response.send_message("📩 You marked the order as submitted!", ephemeral=True)
        await self.ticket_channel.send(f"📩 {self.user.mention}, your order has been submitted! Please review it.")

        # Provide "I'm Satisfied" button for student using a relative import
        from .orders import SatisfiedButtonView
        view = SatisfiedButtonView(self.tutor.id)
        await self.ticket_channel.send("✅ Click below when you are satisfied:", view=view)

        button.disabled = True
        await interaction.message.edit(view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(TutorMatching(bot))