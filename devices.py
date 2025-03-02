class EndDevice:
    def __init__(self, name, mac_address):
        self.name = name
        self.mac_address = mac_address
        self.hub = None

    def connect_to_hub(self, hub):
        self.hub = hub
        hub.add_device(self)

    def send_data(self, receiver_name, message):
        if self.hub:
            return self.hub.transmit_data(self.name, receiver_name, message)
        return "❌ Device not connected to any hub!"
