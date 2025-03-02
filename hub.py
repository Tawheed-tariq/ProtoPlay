class Hub:
    def __init__(self, name):
        self.name = name
        self.devices = {}  # Dictionary of connected devices

    def add_device(self, device):
        """Connects a device to this hub."""
        self.devices[device.name] = device
        device.hub = self  # Assign hub to device

    def transmit_data(self, sender_name, message):
        """Hub broadcasts data to all connected devices except sender."""
        if sender_name not in self.devices:
            return "❌ Sender not found in hub!"
        
        output = []
        for device_name in self.devices:
            if device_name != sender_name:  # Broadcast to all except sender
                output.append(f"📢 {self.name} broadcasting: '{message}' (From {sender_name} to {device_name})")
        
        return "\n".join(output) if output else "❌ No devices connected!"
