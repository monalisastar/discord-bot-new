import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()

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