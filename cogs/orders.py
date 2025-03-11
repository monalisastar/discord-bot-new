import discord
from discord.ext import commands
import asyncio
from database import db  # Firestore from database.py
import re  # Regular expressions for currency parsing

# Constants
# Constants
TRUSTED_TUTOR_ROLE = "Trusted tutor"
TUTOR_CHAT_CHANNEL = "tutor-chat"
TICKET_CATEGORY_ID = 1346355213358862397  # Updated Category ID

class FindTutorView(discord.ui.View):
    """View with a 'Find Tutor' button."""
    def __init__(self, ticket_channel, user, responses):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.user = user
        self.responses = responses

    @discord.ui.button(label="Find Tutor", style=discord.ButtonStyle.green)
    async def find_tutor(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles Find Tutor button click."""
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Only the client who created the ticket can use this.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Searching for a tutor...", ephemeral=True)

        guild = interaction.guild
        tutor_role = discord.utils.get(guild.roles, name=TRUSTED_TUTOR_ROLE)
        tutor_chat = discord.utils.get(guild.text_channels, name=TUTOR_CHAT_CHANNEL)

        if not tutor_role or not tutor_chat:
            await self.ticket_channel.send("❌ Error: No Trusted Tutors or tutor-chat found.")
            return

        tutor_mention = tutor_role.mention
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

        view = ClaimRejectView(self.ticket_channel, self.user)

        # Send to #tutor-chat
        await tutor_chat.send(tutor_mention, embed=embed, view=view)
        #Send DM to all Trusted Tutors
        for tutor in guild.members:
            if tutor_role in tutor.roles:
                try:
                    await tutor.send(embed=embed, view=view)
                except:
                    pass  # Ignore failed DMs

        await self.ticket_channel.send("✅ Tutors have been notified!")

class ClaimRejectView(discord.ui.View):
    """View with 'Claim' and 'Reject' buttons for tutors."""
    def init(self, ticket_channel, user):
        super().init()
        self.ticket_channel = ticket_channel
        self.user = user
        self.claimed = False  # Prevent multiple claims

    @discord.ui.button(label="✅ Claim", style=discord.ButtonStyle.green)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the claim button."""
        tutor = interaction.user  # The tutor who clicked claim
        guild = interaction.guild

        if self.claimed:
            await interaction.response.send_message("⚠️ This ticket has already been claimed!", ephemeral=True)
            return

        self.claimed = True  # Mark ticket as claimed

        # Grant tutor access to the ticket channel
        try:
            await self.ticket_channel.set_permissions(tutor, read_messages=True, send_messages=True)
            await interaction.response.send_message(f"✅ {tutor.mention} has claimed this ticket!", ephemeral=True)

            # Notify the client
            await self.ticket_channel.send(f"🎉 {tutor.mention} has claimed your ticket, {self.user.mention}!")

            # Disable claim button to prevent multiple claims
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.label == "✅ Claim":
                    child.disabled = True
            await interaction.message.edit(view=self)

        except Exception as e:
            await interaction.response.send_message("❌ Failed to update permissions.", ephemeral=True)
            print(f"Error granting access: {e}")

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the reject button."""
        await interaction.response.send_message("❌ Ticket rejected. It remains open for other tutors.", ephemeral=True)
class Orders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Ensure bot instance is stored in the class
        
    def generate_ticket_name(self, user):
        """Generate a unique ticket name for each user."""
        tickets_ref = db.collection("tickets")
        ticket_count = len(tickets_ref.get()) + 1
        return f"{user.name}{ticket_count}"

    async def order(self, interaction: discord.Interaction):
        """Handles order creation process."""
        user = interaction.user
        guild = interaction.guild

        # Find category by ID instead of name
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

        # Ask questions
        responses = await self.ask_questions(ticket_channel, user)
        if responses is None:
            await ticket_channel.delete()  # Delete ticket if user didn't complete questions
            return
        #Show Find Tutor button
        view = FindTutorView(ticket_channel, user, responses)
        await ticket_channel.send("✅ Your order is ready! Click below to find a tutor:", view=view)

    async def ask_questions(self, channel, user):
        """Ask a series of interactive questions and collect responses."""
        def check(m):
            return m.author == user and m.channel == channel

        questions = [
            ("📌 How can we help you today?\n(Assignment, Quiz, Exam, Essay)", "category"),
            ("📚 What is your field of study and level?", "field"),
            ("⏳ When is it due?", "due_date"),
            ("💰 What’s your proposed budget?", "budget"),  # Minimum $20 check hidden
            ("📂 Any additional information?\n(Upload files if needed)", "extra_info")
        ]

        responses = {}

        for question, key in questions:
            embed = discord.Embed(
                title="📋 Order Form",
                description=question,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Please type your response below ⬇️")

            await channel.send(embed=embed)

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=120)

                if key == "budget":
                    budget_value, currency_symbol = self.parse_budget(msg.content)

                    if budget_value is None:
                        await channel.send("⚠️ Please enter a valid budget with a currency symbol (e.g., $30, 50€).")
                        return None  # Cancel process

                    if budget_value < 20:
                        await channel.send("⚠️ The minimum budget is $20 (or equivalent in your currency). You can negotiate later.")

                    responses[key] = f"{currency_symbol}{budget_value}"

                else:
                    responses[key] = msg.content

            except asyncio.TimeoutError:
                await channel.send("⏳ You took too long to respond. Ticket creation cancelled.")
                return None

        return responses

    def parse_budget(self, budget_input):
        """Extracts and validates budget amount and currency from user input."""
        budget_input = budget_input.strip()

#Regular expression to extract numbers (including decimals) and currency symbols
        match = re.search(r"([$£€₹¥₩C$])?(\d+(.\d{1,2})?)", budget_input)

        if not match:
            return None, None  # Invalid input

        currency_symbol = match.group(1) if match.group(1) else "$"  # Default to $
        budget_value = float(match.group(2))

        return budget_value, currency_symbol

async def setup(bot):
    await bot.add_cog(Orders(bot))
    # Order Button
    async def order(self, interaction: discord.Interaction):
        """Handles order ticket creation from the button."""
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(1346355213358862397)  # Ensure this is the correct category ID

        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ Error: Ticket category not found. Contact an admin.", ephemeral=True)
            return

        # Generate unique ticket name
        ticket_name = self.generate_ticket_name(user)

        # Create the private ticket channel
        ticket_channel = await guild.create_text_channel(ticket_name, category=category)
        await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)

        # Welcome message
        await ticket_channel.send(f"Hi {user.mention}, thanks for choosing Hire A Tutor! Please answer these questions.")

        # Ask questions and store responses
        responses = await self.ask_questions(ticket_channel, user)

        if responses:
            # Store in Firebase
            ticket_data = {
                "user_id": user.id,
                "username": user.name,
                "category": responses["category"],
                "field": responses["field"],
                "due_date": responses["due_date"],
                "budget": responses["budget"],
                "extra_info": responses["extra_info"],
                "status": "open"
            }
            db.collection("tickets").document().set(ticket_data)
    #Show "Find Tutor" Button
            await ticket_channel.send(
                "✅ Thank you! Click the Find Tutor button below to proceed.",
                view=FindTutorView(ticket_channel, user, responses)
            ) 
 
# Claim/Reject View
class ClaimRejectView(discord.ui.View):
    def __init__(self, ticket_channel, user):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.user = user

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        tutor = interaction.user
        await self.ticket_channel.send(f"{self.user.mention}, {tutor.mention} has claimed your order. You can now discuss further.")
        
        self.disable_buttons()
        await interaction.message.edit(view=self)  # Update message
        await interaction.response.defer()  # Prevent "interaction failed"

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You have rejected this order.", ephemeral=True)

        self.disable_buttons()
        await interaction.message.edit(view=self)  # Update message
        await interaction.response.defer()

    def disable_buttons(self):
        for button in self.children:
            button.disabled = True


class OrderDeliveredView(discord.ui.View):
    """View with an 'Order Delivered' button for the tutor."""
    def __init__(self, ticket_channel, tutor, student):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.tutor = tutor
        self.student = student

    @discord.ui.button(label="Order Delivered", style=discord.ButtonStyle.green)
    async def order_delivered(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Order Delivered button click by the tutor."""
        if interaction.user != self.tutor:
            await interaction.response.send_message("❌ Only the assigned tutor can mark the order as delivered.", ephemeral=True)
            return

        # Notify the student that the order has been delivered
        await self.ticket_channel.send(f"✅ {self.tutor.mention} has delivered the order. {self.student.mention}, please review or close the ticket.")

        # Add a button for the student to review or close the ticket
        review_button = discord.ui.Button(label="Review Order", style=discord.ButtonStyle.blurple)
        close_button = discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.red)

        # View with Review/Close options
        view = CloseTicketView(self.ticket_channel, self.student, self.tutor, review_button, close_button)
        await self.ticket_channel.send("🔍 Review the delivered order or close the ticket.", view=view)

        # Disable the button after the tutor clicks
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Order Delivered":
                child.disabled = True
        await interaction.message.edit(view=self)


import discord
from discord.ext import commands

# Assuming bot is already initialized somewhere
bot = commands.Bot(command_prefix="!")

class CloseTicketView(discord.ui.View):
    """View with 'Close Ticket' and 'Review Order' buttons for the student."""
    def __init__(self, ticket_channel, student, tutor):
        super().__init__()
        self.ticket_channel = ticket_channel
        self.student = student
        self.tutor = tutor  # Store tutor here

    @discord.ui.button(label="Review Order", style=discord.ButtonStyle.blurple)
    async def review_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the review order button."""
        if interaction.user != self.student:
            await interaction.response.send_message("❌ Only the student can leave a review.", ephemeral=True)
            return

        # Prompt the student to leave a review
        await interaction.response.send_message(f"Please leave a rating and review for {self.tutor.mention}.", ephemeral=True)
        
        # Ask the student to leave their rating and review
        await self.ticket_channel.send("Please leave your rating (1-5) and a detailed review about the tutor.")

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the close ticket button."""
        if interaction.user != self.student:
            await interaction.response.send_message("❌ Only the student can close the ticket.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Closing the ticket. Thanks for using our service, {self.student.mention}!", ephemeral=True)

        # Closing ticket logic
        await self.ticket_channel.send(f"🎉 {self.student.mention} has closed the ticket. The ticket is now closed.")
        await self.ticket_channel.delete()


@bot.event
async def on_message(message):
    # Assuming ticket_channel is properly initialized earlier
    ticket_channel = discord.utils.get(message.guild.text_channels, name="ticket")  # Replace with your actual channel name

    if message.channel.id == ticket_channel.id:
        # Handle review submission
        if message.content.startswith("Rating:"):
            # Capture rating and review text properly
            parts = message.content[len("Rating:"):].strip().split(" ", 1)
            if len(parts) == 2:
                rating = parts[0]  # Extract rating (e.g., 5)
                review = parts[1]  # Extract review text
            else:
                await message.channel.send("❌ Please provide both a rating and a review after 'Rating:'.")
                return

            # Send the review to #review channel
            review_channel = discord.utils.get(message.guild.text_channels, name="review")
            if review_channel:
                embed = discord.Embed(
                    title=f"Review for {message.author.display_name}",  # Use message.author to get the student's name
                    description=f"Rating: {rating}\nReview: {review}",
                    color=discord.Color.blue()
                )
                await review_channel.send(embed=embed)
                
                # Optionally, thank the student
                await message.channel.send("✅ Thank you for your feedback! The ticket will now be closed.")
                
                # Close the ticket
                await message.channel.send(f"🎉 {message.author.mention} has left a review. Closing the ticket.")
                await message.channel.delete()

    # Ensure command processing works after handling custom logic
    await bot.process_commands(message)

# Command to send order button
@commands.command()
async def order(self, ctx):
    """Command to send an order button"""
    await ctx.send("Click below to create an order:", view=Orders.OrderButton(self.bot, ctx.author, self))

async def setup(bot):
    await bot.add_cog(Orders(bot))