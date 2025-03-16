import discord
from discord.ext import commands
import asyncio
import re  # For currency detection and conversion
from database import db  # Firestore Database
import os
from .tutor_matching import TutorMatching  # Use relative import for tutor matching
import logging
from datetime import datetime, timedelta

# Conversion rates to USD (example rates; adjust as needed)
CONVERSION_RATES = {
    "usd": 1.0,
    "$": 1.0,
    "dollar": 1.0,
    "dollars": 1.0,
    "eur": 1.1,    # 1 EUR ~ 1.1 USD
    "€": 1.1,
    "euro": 1.1,
    "euros": 1.1,
    "gbp": 1.3,    # 1 GBP ~ 1.3 USD
    "£": 1.3,
    "pound": 1.3,
    "pounds": 1.3,
    "kes": 0.0073, # 1 KES ~ 0.0073 USD
}

def convert_budget_to_usd(budget_str: str):
    lower_str = budget_str.lower()
    amount_match = re.search(r"(\d+(?:\.\d+)?)", lower_str)
    if not amount_match:
        return None, None
    amount = float(amount_match.group(1))
    
    detected_currency = None
    for key in CONVERSION_RATES.keys():
        if key in lower_str:
            detected_currency = key
            break
    if not detected_currency:
        detected_currency = "usd"
    conversion_rate = CONVERSION_RATES.get(detected_currency, 1.0)
    usd_value = amount * conversion_rate

    conversion_info = (
        f"{detected_currency.upper()} {amount:.2f} => ${usd_value:.2f} USD"
        if detected_currency != "usd"
        else f"${amount:.2f} USD"
    )
    return usd_value, conversion_info

TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "1346355213358862397"))

# --- Review Modal for submitting rating and review ---
class ReviewModal(discord.ui.Modal):
    """Modal for collecting a star rating and a text review."""
    def __init__(self, tutor_id: int):
        super().__init__(title="Submit Review")
        self.tutor_id = tutor_id

        # Star Rating input
        self.rating = discord.ui.TextInput(
            label="Star Rating (1-5)",
            placeholder="Enter a number between 1 and 5",
            max_length=1,
            required=True
        )
        # Review input
        self.review = discord.ui.TextInput(
            label="Review",
            style=discord.TextStyle.long,
            placeholder="Write your review here",
            required=True
        )

        # Add them to the modal
        self.add_item(self.rating)
        self.add_item(self.review)

    async def on_submit(self, interaction: discord.Interaction):
        """Handles the modal submission."""
        try:
            rating_str = self.rating.value.strip()
            rating_int = int(rating_str)
            if rating_int < 1 or rating_int > 5:
                await interaction.response.send_message("⚠️ Please enter a rating between 1 and 5.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("⚠️ Invalid rating. Please enter a number between 1 and 5.", ephemeral=True)
            return

        # Create mention strings so the review looks natural.
        tutor_mention = f"<@{self.tutor_id}>"
        student_mention = f"<@{interaction.user.id}>"

        # Updated channel name to "⭐reviews⭐"
        reviews_channel = discord.utils.get(interaction.guild.text_channels, name="⭐reviews⭐")
        if reviews_channel:
            embed = discord.Embed(
                title="New Review",
                description=(
                    f"{tutor_mention} just received a review!\n\n"
                    f"**Reviewer:** {student_mention}\n"
                    f"**Rating:** {rating_int}/5\n"
                    f"**Review:** {self.review.value}"
                ),
                color=discord.Color.green()
            )
            try:
                await reviews_channel.send(embed=embed)
                await interaction.response.send_message("✅ Your review has been posted!", ephemeral=True)
            except Exception as e:
                logging.error(f"Error posting review: {e}")
                await interaction.response.send_message(f"⚠️ Failed to post review: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Reviews channel not found. Please contact an admin.", ephemeral=True)

# --- Orders Cog ---
class Orders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_last_interaction = {}

    async def rate_limit_check(self, user_id: int):
        """Check if the user is rate-limited (e.g., no spamming)."""
        current_time = datetime.now()
        if user_id in self.user_last_interaction:
            last_time = self.user_last_interaction[user_id]
            if current_time - last_time < timedelta(minutes=5):  # 5-minute cooldown
                return False
        self.user_last_interaction[user_id] = current_time
        return True

    async def order(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        # Check for rate limit (e.g., user spamming orders)
        if not await self.rate_limit_check(user.id):
            await interaction.response.send_message("⚠️ You need to wait a while before creating another order.", ephemeral=True)
            return

        # Get the ticket category
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("⚠️ Ticket category not found! Please contact an admin.", ephemeral=True)
            return

        ticket_name = f"order-{user.name}".replace(" ", "-").lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Create ticket channel with error handling
        try:
            ticket_channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)
        except discord.Forbidden as e:
            await interaction.response.send_message("⚠️ Insufficient permissions to create the ticket channel.", ephemeral=True)
            logging.error(f"Permission error when creating ticket channel: {e}")
            return

        # Send welcome message with error handling
        try:
            welcome_embed = discord.Embed(
                title="🎟️ Your Order Ticket is Ready!",
                description=f"Hello {user.mention}, welcome to **Hire A Tutor**!\n\nKindly answer the following questions so we can better assist you.",
                color=discord.Color.from_rgb(30, 144, 255)
            )
            welcome_embed.set_footer(text="You have 1 hour per question.")
            await ticket_channel.send(embed=welcome_embed)
        except Exception as e:
            logging.error(f"Error sending welcome message: {e}")
            await interaction.response.send_message(f"⚠️ Error sending welcome message: {str(e)}", ephemeral=True)
            return

        await self.ask_order_questions(user, ticket_channel)

    async def ask_order_questions(self, user: discord.User, channel: discord.TextChannel):
        questions = [
            "How can we help you today? (e.g., assignment, essay, exam, quiz, or project)",
            "What subject or field is this related to?",
            "What is your proposed budget? (Any format; our bot will convert it to USD)",
            "Do you have any additional materials or information to share?"
        ]
        answers = {}

        def check(m: discord.Message):
            return m.author == user and m.channel == channel

        for question in questions:
            try:
                await channel.send(embed=discord.Embed(
                    title="❓ Question",
                    description=question,
                    color=discord.Color.from_rgb(72, 209, 204)
                ))
                msg = await self.bot.wait_for('message', check=check, timeout=3600)
                answers[question] = msg.content
            except asyncio.TimeoutError:
                await channel.send(embed=discord.Embed(
                    title="⏳ Timeout",
                    description="You took too long to respond. Please restart the order process.",
                    color=discord.Color.red()
                ))
                await channel.delete()
                return

        budget_input = answers[questions[2]]
        usd_value, conversion_info = convert_budget_to_usd(budget_input)
        if usd_value is None or usd_value < 20:  # Ensuring minimum budget
            await channel.send(embed=discord.Embed(
                title="⚠️ Budget Issue",
                description=f"Budget after conversion: {conversion_info}. Minimum is $20.",
                color=discord.Color.red()
            ))
            await channel.delete()
            return

        order_data = {
            "student": user.id,
            "help_request": answers[questions[0]],
            "subject": answers[questions[1]],
            "budget": conversion_info,
            "additional_materials": answers[questions[3]],
            "status": "Pending Tutor"
        }

        try:
            db.collection("orders").document(str(user.id)).set(order_data)
        except Exception as e:
            logging.error(f"Error saving order to Firestore: {e}")
            await channel.send("⚠️ There was an error saving your order. Please try again later.")
            await channel.delete()
            return

        try:
            await channel.send(embed=discord.Embed(
                title="✅ Order Created!",
                description="Your order has been successfully created!",
                color=discord.Color.green()
            ))
        except Exception:
            pass

        # Hand over to TutorMatching to find a tutor
        tutor_matching_cog = self.bot.get_cog("TutorMatching")
        if tutor_matching_cog:
            try:
                await tutor_matching_cog.match_tutor(channel, user)
            except Exception as e:
                await channel.send(f"⚠️ Error in tutor matching: {str(e)}")
        else:
            await channel.send("⚠️ Tutor matching system is unavailable. Please contact an admin.")

# --- Satisfied Button View ---
class SatisfiedButtonView(discord.ui.View):
    """View for collecting review and providing options to close or escalate the order."""
    def __init__(self, tutor_id: int):
        super().__init__(timeout=300)  # Timeout after 5 minutes
        self.tutor_id = tutor_id

    @discord.ui.button(label="Submit Review", style=discord.ButtonStyle.primary, emoji="📝")
    async def submit_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Opens a modal to collect star rating and review."""
        try:
            modal = ReviewModal(self.tutor_id)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logging.error(f"Error opening review modal: {e}")
            await interaction.response.send_message(
                f"⚠️ An error occurred while opening the review modal: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="❌ Close Order", style=discord.ButtonStyle.red)
    async def close_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and close the order."""
        try:
            await interaction.response.send_message(
                "⚠️ Are you sure you want to close this order? Confirm with another button!",
                ephemeral=True
            )
            confirm_button = discord.ui.Button(label="✅ Confirm Close", style=discord.ButtonStyle.green)
            confirm_view = discord.ui.View(timeout=30)
            confirm_view.add_item(confirm_button)

            async def confirm_close(confirm_interaction: discord.Interaction):
                await confirm_interaction.response.send_message("✅ The order has been closed.", ephemeral=True)
                await interaction.channel.delete()

            confirm_button.callback = confirm_close
            await interaction.followup.send("Please confirm closing the order.", view=confirm_view)
        except Exception as e:
            logging.error(f"Error closing the order: {e}")
            await interaction.followup.send(
                f"⚠️ An error occurred while closing the order: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="🚨 Escalate Issue", style=discord.ButtonStyle.danger)
    async def escalate_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Escalate issue to admin."""
        try:
            admin_channel = discord.utils.get(interaction.guild.text_channels, name="admin-issues")
            if admin_channel:
                await admin_channel.send(
                    f"🚨 Escalated Issue: {interaction.user.mention} is not satisfied with the order! Tutor ID: {self.tutor_id}"
                )
                await interaction.response.send_message(
                    "🚨 The issue has been escalated to the admin!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "⚠️ Admin channel not found! Please contact an admin directly.",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Error escalating issue: {e}")
            await interaction.response.send_message(
                f"⚠️ An error occurred while escalating the issue: {str(e)}",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Orders(bot))



















