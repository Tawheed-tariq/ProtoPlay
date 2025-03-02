from devices import EndDevice
from hub import Hub

hubs = {}  # Dictionary of available hubs
devices = {}  # Dictionary of connected devices
direct_links = {}  # Stores direct connections as {device1: device2}

def create_hub(name):
    """Creates a new hub."""
    if name in hubs:
        return "❌ Hub already exists!"
    hubs[name] = Hub(name)
    return f"✅ Hub '{name}' created successfully!"

def add_device(name, mac, hub_name):
    """Creates a device and connects it to a specified hub."""
    if name in devices:
        return "❌ Device already exists!"
    if hub_name not in hubs:
        return "❌ Hub not found!"
    
    new_device = EndDevice(name, mac)
    new_device.connect_to_hub(hubs[hub_name])  # Connect to the chosen hub
    devices[name] = new_device
    return f"✅ {name} connected to {hub_name}!"

def get_devices():
    """Returns a list of connected devices."""
    return [{"Device Name": d.name, "MAC Address": d.mac_address, "Hub": d.hub.name if d.hub else "None"} for d in devices.values()]

def create_direct_link(device1, device2):
    """Creates a direct connection between two devices."""
    if device1 not in devices or device2 not in devices:
        return "❌ One or both devices not found!"
    
    direct_links[device1] = device2
    direct_links[device2] = device1
    return f"🔗 Direct link created between {device1} and {device2}!"

def send_data(sender, receiver, message, method):
    """Send data using direct link or hub."""
    if sender not in devices or receiver not in devices:
        return "❌ Invalid sender or receiver!"

    if method == "Direct Link":
        if sender in direct_links and direct_links[sender] == receiver:
            return f"🔗 Direct Connection: {sender} -> {receiver}: {message}"
        return "❌ No direct link found!"

    elif method == "Hub":
        if devices[sender].hub and devices[receiver].hub and devices[sender].hub == devices[receiver].hub:
            return devices[sender].hub.transmit_data(sender, message)
        return "❌ Devices are not in the same hub!"

    return "❌ Invalid transmission method!"

def get_hubs():
    """Returns a list of available hubs."""
    return list(hubs.keys())
