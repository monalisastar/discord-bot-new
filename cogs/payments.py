import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import firestore
import json

# Initialize Firebase Firestore
db = firestore.client()

# Constants
BITCOIN_ADDRESS = "your-bitcoin-address-here"
PAYPAL_EMAIL = "your-paypal-email@example.com"
REMITLY_DETAILS = "Remitly payment details here..."
BITCOIN_GUIDE_LINKS = {
    "US": "https://cash.app/help/3101-buying-bitcoin",
    "UK": "https://www.coinbase.com/how-to-buy/bitcoin",
    "India": "https://wazirx.com/how-to-buy-bitcoin",
    "Nigeria": "https://binance.com/en/how-to-buy/bitcoin",
    "Other": "https://www.bitcoin.org/en/buy"
}
PAYPAL_SURCHARGE_PERCENTAGE = 20
class PaymentView(discord.ui.View):
    """View with Bitcoin, Remitly, and PayPal buttons."""
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
    @discord.ui.button(label="Bitcoin", style=discord.ButtonStyle.gray, emoji="💰")
    async def bitcoin_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Asks the user for their country and provides Bitcoin purchasing guidelines."""
        await interaction.response.send_message("🌍 Which country are you from?", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60)
            country = msg.content.strip()
            guide_link = BITCOIN_GUIDE_LINKS.get(country, BITCOIN_GUIDE_LINKS["Other"])
            await interaction.followup.send(
                f"💰 Bitcoin Payment Details:\n"
                f"🔹 Address: {BITCOIN_ADDRESS}\n"
                f"🔹 How to buy in {country}: [Click here]({guide_link})",
                ephemeral=True
            )
        except:
            await interaction.followup.send("⚠️ You didn't respond in time. Please try again.", ephemeral=True)

    @discord.ui.button(label="Remitly (Recommended)", style=discord.ButtonStyle.green)
    async def remitly_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Provides Remitly payment details."""
        await interaction.response.send_message(f"📌 Remitly Payment Details:\n{REMITLY_DETAILS}", ephemeral=True)

    @discord.ui.button(label="PayPal (+20% Fee)", style=discord.ButtonStyle.blurple, emoji="💳")
    async def paypal_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Displays PayPal details and surcharge notice."""
        await interaction.response.send_message(
            f"📌 PayPal Payment Details:\n"
            f"🔹 Email: {PAYPAL_EMAIL}\n"
            f"🔹 20% surcharge applies\n"
            f"⚠️ Please calculate the total amount accordingly.",
            ephemeral=True
        )

class Payment(commands.Cog):
    def init(self, bot):
        self.bot = bot

    @commands.command(name="pay-hireatutor")
    async def pay_command(self, ctx):
        """Sends payment options (Bitcoin, Remitly, PayPal)."""
        student_id = str(ctx.author.id)
        embed = discord.Embed(
            title="💰 Payment Options",
            description="Please select your preferred payment method:",
            color=discord.Color.gold()
        )
        view = PaymentView(student_id)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Payment(bot))    
    
    
    @commands.command(name="upload-proof")
    async def upload_proof(self, ctx):
        """Allows students to upload payment proof (screenshot or transaction ID)."""
        student_id = str(ctx.author.id)
        await ctx.send("📌 Please upload a screenshot or enter your transaction ID.")

        def check(m):
            return m.author == ctx.author and (m.attachments or m.content)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=120)
            proof_data = {
                "student_id": student_id,
                "proof": msg.attachments[0].url if msg.attachments else msg.content
            }
            db.collection("payments").document(student_id).set(proof_data)
            await ctx.send("✅ Payment proof uploaded. A tutor will be notified shortly.")
            # Notify assigned tutor
            tutor_id = self.get_assigned_tutor(student_id)
            if tutor_id:
                tutor = self.bot.get_user(tutor_id)
                if tutor:
                    await tutor.send(f"📢 Your student {ctx.author.mention} has uploaded payment proof.")

        except:
            await ctx.send("⚠️ You didn't upload proof in time. Please try again.")

    @commands.command(name="verify-payment")
    @commands.has_permissions(administrator=True)
    async def verify_payment(self, ctx, student_id: str):
        """Admins manually verify payments."""
        payment_doc = db.collection("payments").document(student_id).get()

        if payment_doc.exists:
            db.collection("payments").document(student_id).update({"verified": True})
            await ctx.send(f"✅ Payment verified for student <@{student_id}>.")
            await self.generate_receipt(ctx, student_id)
        else:
            await ctx.send("❌ No payment proof found for this student.")

    async def generate_receipt(self, ctx, student_id):
        """Sends a simple receipt after admin verification."""
        student = self.bot.get_user(int(student_id))
        if student:
            await student.send("📜 **Receipt**\n✅ Your payment has been verified. Thank you for using our service!")

    def get_assigned_tutor(self, student_id):
        """Fetch the assigned tutor for a student (mock function for now)."""
        return None  # Replace with actual database query

async def setup(bot):
    await bot.add_cog(Payment(bot))
