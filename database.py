import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

# Use absolute path for serviceAccount.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
cred_path = os.path.join(BASE_DIR, "serviceAccount.json")  # Full path

# Check if Firebase is already initialized
if not firebase_admin._apps:
    # Load Firebase credentials
    cred = credentials.Certificate(cred_path)
    
    # Initialize Firebase app **with storage bucket explicitly set**
    firebase_admin.initialize_app(cred, {"storageBucket": f"{cred.project_id}.appspot.com"})

# Get Firestore database instance
db = firestore.client()

# Get Firebase Storage bucket instance
bucket = storage.bucket()  # Automatically uses default bucket

# Function to create a new ticket in Firestore
def create_ticket(user_id, username, ticket_number, channel_id):
    ticket_name = f"{username}{ticket_number}"  # Create unique ticket name
    ticket_ref = db.collection("orders").document(ticket_name)  # Store under 'orders' collection

    ticket_ref.set({
        "user_id": user_id,
        "username": username,
        "ticket_number": ticket_number,
        "channel_id": channel_id,
        "status": "open",
    })

    return ticket_name  # Return the ticket name (used in orders.py)