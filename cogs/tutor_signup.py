import discord
from discord.ext import commands
from database import db  # Firestore
import logging
import asyncio

TUTOR_SIGNUP_CATEGORY = "Tutor Applications"

class TutorSignup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_ticket_name(self, user):
        try:
            # Generate ticket name based on the number of applications
            applications_ref = db.collection("tutor_applications")
            application_count = len(applications_ref.get()) + 1
            return f"tutor-{user.name}{application_count}"
        except Exception as e:
            logging.error(f"Error generating ticket name for {user.name}: {str(e)}")
            return f"tutor-{user.name}-1"  # Fallback ticket name

    async def ask_questions(self, channel, user):
        """This function handles asking the questions and getting the responses"""
        def check(m):
            return m.author == user and m.channel == channel

        questions = [
            ("What subject(s) can you tutor?", "subjects"),
            ("What is your highest level of education?", "education"),
            ("Do you have any tutoring experience? (Yes/No)", "experience"),
            ("Why do you want to be a tutor?", "motivation"),
            ("Please upload any relevant certificates or documents.", "documents"),
            ("You will make a 40$ tutor admission fee, a one-time payment.", "payment")
        ]

        responses = {}

        for question, key in questions:
            await channel.send(question)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=180)  # Timeout extended for 3 minutes
                if msg.attachments:
                    responses[key] = msg.attachments[0].url  # Store file URL
                else:
                    responses[key] = msg.content
            except asyncio.TimeoutError:
                await channel.send(f"⏳ You took too long to respond. Your application has been cancelled.")
                logging.error(f"Timeout occurred while waiting for user {user.name}'s response.")
                return None
            except Exception as e:
                logging.error(f"Error during asking question '{question}' to {user.name}: {str(e)}")
                await channel.send(f"⚠️ An error occurred while asking the question: {str(e)}")
                return None

        return responses

    class SignupButton(discord.ui.View):
        def __init__(self, bot, user):
            super().__init__()
            self.bot = bot
            self.user = user

        @discord.ui.button(label="Sign Up to Be a Tutor", style=discord.ButtonStyle.primary)
        async def signup(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handles the signup process when the user clicks the button"""
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name=TUTOR_SIGNUP_CATEGORY)

            if not category:
                try:
                    category = await guild.create_category(TUTOR_SIGNUP_CATEGORY)
                except discord.Forbidden as e:
                    logging.error(f"Error creating category {TUTOR_SIGNUP_CATEGORY}: {str(e)}")
                    await interaction.response.send_message("⚠️ I don't have permission to create categories.")
                    return

            try:
                ticket_name = self.generate_ticket_name(self.user)
                ticket_channel = await guild.create_text_channel(ticket_name, category=category)
                await ticket_channel.set_permissions(self.user, read_messages=True, send_messages=True)
            except discord.Forbidden as e:
                logging.error(f"Error creating channel for user {self.user.name}: {str(e)}")
                await interaction.response.send_message("⚠️ I don't have permission to create channels.")
                return
            except Exception as e:
                logging.error(f"Error during channel creation for user {self.user.name}: {str(e)}")
                await interaction.response.send_message("⚠️ An unexpected error occurred.")
                return

            await ticket_channel.send(f"Hi {self.user.mention}, welcome to the tutor application process! Please answer the following questions.")

            responses = await TutorSignup.ask_questions(self.bot, ticket_channel, self.user)

            if responses:
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
                try:
                    db.collection("tutor_applications").document().set(application_data)
                    await ticket_channel.send(f"Thank you for applying, {self.user.mention}! Our team will review your application and contact you soon.")
                except Exception as e:
                    logging.error(f"Error saving application data for {self.user.name}: {str(e)}")
                    await ticket_channel.send("⚠️ An error occurred while saving your application. Please try again later.")

async def setup(bot):
    await bot.add_cog(TutorSignup(bot))


