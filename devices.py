class EndDevice:
    def __init__(self, device_id, mac_address):
        self.id = device_id
        self.mac = mac_address
        self.connected_to = None  # Hub, Switch, or direct connection

    def send(self, data, destination, layer="physical"):
        if layer == "data_link":
            # Create a frame for Data Link Layer
            frame = Frame(self.mac, destination.mac, data)
            if self.connected_to:
                self.connected_to.transmit(self, frame, destination)
        else:
            # Physical Layer: send raw data
            if self.connected_to:
                self.connected_to.transmit(self, data, destination)