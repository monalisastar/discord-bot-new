import discord
from discord.ext import commands
from database import db  # Firestore

# Category where tutor applications will be created
TUTOR_SIGNUP_CATEGORY = "Tutor Applications"

class TutorSignup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function to generate ticket name
    def generate_ticket_name(self, user):
        applications_ref = db.collection("tutor_applications")
        application_count = len(applications_ref.get()) + 1
        return f"tutor-{user.name}{application_count}"

    # Function to ask tutor application questions
    async def ask_questions(self, channel, user):
        def check(m):
            return m.author == user and m.channel == channel

        questions = [
            ("What subject(s) can you tutor?", "subjects"),
            ("What is your highest level of education?", "education"),
            ("Do you have any tutoring experience? (Yes/No)", "experience"),
            ("Why do you want to be a tutor?", "motivation"),
            ("Please upload any relevant certificates or documents.", "documents")
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
                await channel.send("You took too long to respond. Application cancelled.")
                return None

        return responses

    # Sign-up button interaction
    class SignupButton(discord.ui.View):
        def __init__(self, bot, user):
            super().__init__()
            self.bot = bot
            self.user = user

        @discord.ui.button(label="Sign Up to Be a Tutor", style=discord.ButtonStyle.primary)
        async def signup(self, interaction: discord.Interaction, button: discord.ui.Button):
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name=TUTOR_SIGNUP_CATEGORY)

            if not category:
                category = await guild.create_category(TUTOR_SIGNUP_CATEGORY)

            # Create a private tutor application ticket
            ticket_name = f"tutor-{self.user.name}{len(db.collection('tutor_applications').get()) + 1}"
            ticket_channel = await guild.create_text_channel(ticket_name, category=category)

            # Set permissions for user
            await ticket_channel.set_permissions(self.user, read_messages=True, send_messages=True)

            await ticket_channel.send(f"Hi {self.user.mention}, welcome to the tutor application process! Please answer the following questions.")

            # Ask questions
            responses = await TutorSignup.ask_questions(self.bot, ticket_channel, self.user)

            if responses:
                # Store application in Firestore
                application_data = {
                    "user_id": self.user.id,
                    "username": self.user.name,
                    "subjects": responses["subjects"],
                    "education": responses["education"],
                    "experience": responses["experience"],
                    "motivation": responses["motivation"],
                    "documents": responses["documents"],
                    "status": "pending"
                }
                db.collection("tutor_applications").document().set(application_data)

                await ticket_channel.send(f"Thank you for applying, {self.user.mention}! Our team will review your application and contact you soon.")

# Setup function for cog
async def setup(bot):
    await bot.add_cog(TutorSignup(bot))
