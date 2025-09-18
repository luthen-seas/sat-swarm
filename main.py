import time
from nostr.key import PrivateKey
from nostr.relay_manager import RelayManager
from nostr.event import Event
from blue_wallet_client import BlueWalletClient  # NEW: Import Lightning client

# NEW: Lightning setup (use input for creds in MVP; secure later)
login = input("Enter Blue Wallet login: ")
password = input("Enter Blue Wallet password: ")
bw_client = BlueWalletClient(bluewallet_login=login, bluewallet_password=password)

# Generate or load keys (like your agent's identity)
private_key = PrivateKey()  # Creates a new one each run; save for persistence later
public_key = private_key.public_key.hex()

# Set up relay manager (decentralized servers for events)
relay_manager = RelayManager()
relay_manager.add_relay("wss://relay.damus.io")  # Public relay; add more for robustness
relay_manager.open_connections({"cert_reqs": 0})  # Skip cert checks for simplicity
time.sleep(1.25)  # Wait for connections

# Create a task event (custom kind=30001 for tasks)
task_content = {
    "description": "Optimize supply chain simulation",
    "max_sats": 1000,
    "deadline": "5 minutes"
}
event = Event(
    public_key=public_key,
    content=str(task_content),  # JSON-like string
    kind=30001  # Custom event type for tasks
)
private_key.sign_event(event)

# Publish the event
relay_manager.publish_event(event)
time.sleep(1)  # Wait for publish

print("Task posted! Event ID:", event.id)

# NEW: Create a Lightning invoice for the task (e.g., 500 sats bid)
invoice_res = bw_client.create_invoice(amt=500, memo=f"Bid for task {event.id}")
payment_request = invoice_res["payment_request"]
r_hash = invoice_res["r_hash"]
print("Generated Lightning invoice for bid:", payment_request)

# Subscribe to bids replying to our task (kind=30002, tagged with #e to the task ID)
filters = [{"kinds": [30002], "#e": [event.id]}]  # Listen for bids on this event
subscription_id = "bid_sub"  # Unique ID for this subscription
relay_manager.add_subscription(subscription_id, filters)

# Poll for incoming messages (simple loop for MVP; run for ~30 seconds now)
print("Listening for bids and checking invoice payment...")
start_time = time.time()
while time.time() - start_time < 30:  # Listen longer for payment
    while relay_manager.message_pool.has_events():
        msg = relay_manager.message_pool.get_event()
        if msg.event.kind == 30002:  # Check it's a bid
            print("Received bid event!")
            print("Bidder Pubkey:", msg.event.public_key)
            print("Bid Content:", msg.event.content)
            print("Bid ID:", msg.event.id)

    # NEW: Check if invoice is paid
    invoice_status = bw_client.lookup_invoice(r_hash=r_hash)
    if invoice_status["ispaid"]:
        print("Invoice paid! Bid accepted.")
        break  # Stop listening once paid

    time.sleep(1)  # Check every second

print("Listening stopped.")

relay_manager.close_connections()