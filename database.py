import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use the serviceAccount.json file from the same directory as this file
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccount.json")
logging.info(f"🔍 Checking for serviceAccount.json at: {file_path}")

if not os.path.exists(file_path):
    logging.error(f"❌ File not found at: {file_path}")
    exit(1)  # Exit if the file isn't found
else:
    logging.info(f"✅ File found at: {file_path}")

try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read()
        logging.info("✅ Successfully read serviceAccount.json!")
except Exception as e:
    logging.error(f"⚠️ Error reading serviceAccount.json: {e}")

# Initialize Firebase if it's not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(file_path)
        firebase_admin.initialize_app(cred)
        logging.info("✅ Firebase initialized.")
    except Exception as e:
        logging.error(f"❌ Error initializing Firebase: {e}")
        exit(1)  # Exit the script if Firebase initialization fails

# Get Firestore database instance
db = firestore.client()

def create_ticket(user_id, username, ticket_number, channel_id):
    """Creates a new ticket in the Firestore database."""
    ticket_name = f"{username}{ticket_number}"  # Create unique ticket name
    ticket_ref = db.collection("orders").document(ticket_name)  # Store under 'orders' collection

    try:
        ticket_ref.set({
            "user_id": user_id,
            "username": username,
            "ticket_number": ticket_number,
            "channel_id": channel_id,
            "status": "open",
        })
        logging.info(f"✅ Created ticket: {ticket_name}")
        return ticket_name  # Return the ticket name (used in orders.py)
    except Exception as e:
        logging.error(f"❌ Error creating ticket: {ticket_name}. Error: {e}")
        return None  # Return None if ticket creation fails







