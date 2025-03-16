import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import firestore
import os
import logging
import asyncio
from datetime import datetime, timedelta

# Initialize Firebase Firestore
db = firestore.client()

# Admin/Moderator role to be tagged for help (set your role ID here or via env)
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "<@&1125789773546659860>")  # Admin role

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Crypto Addresses ---
CRYPTO_ADDRESSES = {
    "BTC": "1DVwEnVaHbM5PWLzPTVKd9tHn3Wcckw7Dh",
    "ETH": "0xd11412def47a98eb1221b07a5400d9ff36e976de",
    "USDT": "0xd11412def47a98eb1221b07a5400d9ff36e976de",  # same as ETH address in this example
    "TRX": "TCW5k8N59vGPWFTvMufYw3h63HbTV6cWpr"
}

# --- Cryptocurrency Icons ---
CRYPTO_ICONS = {
    "BTC": "https://example.com/btc_icon.png",  # Replace with actual URLs for logos
    "ETH": "https://example.com/eth_icon.png",
    "USDT": "https://example.com/usdt_icon.png",
    "TRX": "https://example.com/trx_icon.png"
}

# --- Soft Timeout Monitoring Task ---
async def monitor_timeout(interaction: discord.Interaction, timeout_duration: timedelta = timedelta(hours=48)):
    start_time = datetime.now()
    
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        if datetime.now() - start_time >= timeout_duration:
            # Timeout reached, inform the user
            await interaction.followup.send(
                f"Hey {interaction.user.mention}, your payment session has expired due to inactivity.",
                ephemeral=True
            )
            break

# --- Crypto Payment Buttons ---
class CryptoButtonsView(discord.ui.View):
    def __init__(self, author_id: int, amount: float):
        super().__init__(timeout=1800)  # 30 minutes
        self.author_id = author_id
        self.amount = amount

    @discord.ui.button(label="💰 Bitcoin (BTC)", style=discord.ButtonStyle.green)
    async def bitcoin_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            # BTC Payment Embed
            embed = discord.Embed(title="🔗 Bitcoin Payment", color=discord.Color.gold())
            embed.set_thumbnail(url=CRYPTO_ICONS["BTC"])
            embed.description = (
                f"To complete your payment, send **${self.amount} in BTC** to the following address:\n\n"
                f"📍 **Address:** `{CRYPTO_ADDRESSES['BTC']}`\n\n"
                "After payment, please **send a screenshot as proof** of completion."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in bitcoin_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="💰 Ethereum (ETH)", style=discord.ButtonStyle.blurple)
    async def ethereum_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            # ETH Payment Embed
            embed = discord.Embed(title="🔗 Ethereum Payment", color=discord.Color.green())
            embed.set_thumbnail(url=CRYPTO_ICONS["ETH"])
            embed.description = (
                f"To complete your payment, send **${self.amount} in ETH** to the following address:\n\n"
                f"📍 **Address:** `{CRYPTO_ADDRESSES['ETH']}`\n\n"
                "After payment, please **send a screenshot as proof** of completion."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in ethereum_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="💰 TRON (TRX)", style=discord.ButtonStyle.primary)
    async def tron_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            # TRX Payment Embed
            embed = discord.Embed(title="🔗 TRON Payment", color=discord.Color.blue())
            embed.set_thumbnail(url=CRYPTO_ICONS["TRX"])
            embed.description = (
                f"To complete your payment, send **${self.amount} in TRX** to the following address:\n\n"
                f"📍 **Address:** `{CRYPTO_ADDRESSES['TRX']}`\n\n"
                "After payment, please **send a screenshot as proof** of completion."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in tron_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="💰 USDT (Tether)", style=discord.ButtonStyle.green)
    async def usdt_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            # USDT Payment Embed
            embed = discord.Embed(title="🔗 USDT Payment", color=discord.Color.orange())
            embed.set_thumbnail(url=CRYPTO_ICONS["USDT"])
            embed.description = (
                f"To complete your payment, send **${self.amount} in USDT** to the following address:\n\n"
                f"📍 **Address:** `{CRYPTO_ADDRESSES['USDT']}`\n\n"
                "After payment, please **send a screenshot as proof** of completion."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in usdt_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

# --- Main Payment View with Crypto Options ---
class PaymentView(discord.ui.View):
    def __init__(self, student_id: int, amount: float):
        super().__init__(timeout=1800)  # 30 minutes
        self.student_id = student_id
        self.amount = amount

    @discord.ui.button(label="💰 Pay with Crypto", style=discord.ButtonStyle.primary)
    async def crypto_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.student_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            view = CryptoButtonsView(interaction.user.id, amount=self.amount)
            await interaction.response.send_message(
                "Please select your cryptocurrency to view payment details:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Error in crypto_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="💳 Pay with PayPal", style=discord.ButtonStyle.blurple)
    async def paypal_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.student_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            # Apply a 25% surcharge to discourage the use of PayPal.
            surcharge_amount = round(self.amount * 1.25, 2)
            embed = discord.Embed(title="📩 Pay with PayPal", color=discord.Color.blue())
            embed.description = (
                f"Due to a 25% surcharge, the total for PayPal payments is **${surcharge_amount} USD**.\n\n"
                f"To pay via PayPal, please manually send **${surcharge_amount} USD** to:\n\n"
                f"📧 **PayPal Email:** `trizer.trio56@gmail.com`\n\n"
                "After sending the payment, **provide a screenshot** for confirmation."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in paypal_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="📨 Pay with Remitly (✅ Recommended)", style=discord.ButtonStyle.green)
    async def remitly_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.student_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            embed = discord.Embed(title="📌 Remitly Payment Instructions", color=discord.Color.green())
            embed.add_field(name="1️⃣ Register on Remitly", value="[Click Here](https://www.remitly.com/us/en/kenya)", inline=False)
            embed.add_field(name="2️⃣ Country to Send", value="🇰🇪 **KENYA**", inline=True)
            embed.add_field(name="3️⃣ Delivery Method", value="📲 **Mobile Money (MPESA)**", inline=True)
            embed.add_field(name="4️⃣ Recipient Name", value="👤 **Brian Njata**", inline=False)
            embed.add_field(name="5️⃣ Recipient Phone", value="📞 **0706472326**", inline=False)
            embed.set_footer(text="Remitly is the recommended payment method.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in remitly_payment: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

    @discord.ui.button(label="❓ Need Help?", style=discord.ButtonStyle.secondary)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.student_id:
                await interaction.response.send_message("This button isn’t for you.", ephemeral=True)
                return

            await interaction.response.send_message(
                f"{ADMIN_ROLE} Assistance requested by {interaction.user.mention}.",
                ephemeral=False
            )
        except Exception as e:
            logging.error(f"Error in help_button: {e}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

# --- Payment Cog ---
class Payment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pay")
    async def pay_command(self, ctx, payment_type: str, order_id: str = None):
        """
        Usage: !pay hireatutor [order_id]
        If no order_id is provided, the bot uses your Discord user ID to look up your pending order.
        """
        try:
            if payment_type.lower() == "hireatutor":
                # Automatically use the user's ID if no order_id is provided.
                if not order_id:
                    order_id = str(ctx.author.id)
                    
                # Fetch the order from Firestore using the order_id.
                doc_ref = db.collection("orders").document(order_id)
                doc = doc_ref.get()
                if not doc.exists:
                    await ctx.send("No pending order found for you. Please create an order first.")
                    return

                order_data = doc.to_dict()
                amount = order_data.get("amount")  # Use the agreed amount
                if amount is None:
                    await ctx.send("Invalid order amount. Please check your order details.")
                    return

                logging.info(f"User {ctx.author} requested payment for order {order_id} with amount ${amount}")

                embed = discord.Embed(title="💰 Payment Options", color=discord.Color.gold())
                embed.description = (
                    f"Please select your preferred payment method below for order **{order_id}**.\n"
                    f"**Total Due:** ${amount}\n\n"
                    "1. **Crypto Payment**\n"
                    "2. **PayPal Payment**\n"
                    "3. **Remitly Payment**\n\n"
                    "Need help? Click the **Need Help?** button."
                )

                view = PaymentView(ctx.author.id, amount=amount)
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send("Invalid payment type. Usage: `!pay hireatutor [order_id]`")
        except Exception as e:
            logging.error(f"Error in pay_command: {e}")
            await ctx.send("An error occurred. Please try again later.")

async def setup(bot):
    await bot.add_cog(Payment(bot))








