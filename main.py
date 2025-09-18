import time
from nostr.key import PrivateKey
from nostr.relay_manager import RelayManager
from nostr.event import Event

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
    "description": "Write a poem about Bitcoin from the voice of Hal Finney",
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
relay_manager.close_connections()