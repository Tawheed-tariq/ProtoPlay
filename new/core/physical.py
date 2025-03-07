# core/physical.py

class Entity:
    """Base class for all network entities (devices, hubs)"""
    def __init__(self, id):
        self.id = id
        self.connected_to = []  # List of connected entities
        
    def connect(self, entity):
        """Connect this entity to another entity"""
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            return True
        return False
    
    def disconnect(self, entity):
        """Disconnect this entity from another entity"""
        if entity in self.connected_to:
            self.connected_to.remove(entity)
            return True
        return False

class EndDevice(Entity):
    """Represents an end device (computer, server, etc.) in the network"""
    def __init__(self, id, mac):
        super().__init__(id)
        self.mac = mac
        self.received_data = []  # Store received data
        
    def send(self, data, destination, layer="physical"):
        """Send data to a destination device at the specified layer"""
        if layer == "physical":
            # At physical layer, we just send bits
            # Check if we're directly connected to the destination
            if destination in self.connected_to:
                destination.receive(data, self)
                return True
                
            # If not directly connected, check if we're connected to a hub
            for entity in self.connected_to:
                if isinstance(entity, Hub):
                    # Forward through the hub
                    return entity.forward(data, self, destination)
            
            return False
        else:
            # Higher layer handling would go here
            pass
    
    def receive(self, data, source):
        """Receive data from a source device"""
        self.received_data.append({
            "data": data,
            "source": source.id
        })
        print(f"Device {self.id} received data: {data} from {source.id}")
        return True
    
    def __str__(self):
        return f"Device(id={self.id}, mac={self.mac})"

class Hub(Entity):
    """Represents a hub in the network that forwards signals to all connected devices"""
    def __init__(self, id):
        super().__init__(id)
        
    def forward(self, data, source, destination=None):
        """
        Forward data from source to all connected devices except the source
        In a hub, data is forwarded to all devices regardless of the destination
        """
        success = False
        
        # A hub broadcasts to all connected devices except the source
        for device in self.connected_to:
            if device != source:  # Don't send back to sender
                if isinstance(device, EndDevice):
                    device.receive(data, source)
                    # If this device is our destination, mark success
                    if device == destination:
                        success = True
                elif isinstance(device, Hub):
                    # Forward through connected hubs (avoiding loops)
                    hub_success = device.forward(data, source, destination)
                    if hub_success and destination is not None:
                        success = True
        
        return success if destination is not None else True
    
    def __str__(self):
        return f"Hub(id={self.id})"

class Network:
    """Represents the entire network"""
    def __init__(self):
        self.devices = []
        self.hubs = []
        
    def add_device(self, device):
        """Add a device to the network"""
        if device not in self.devices:
            self.devices.append(device)
            return True
        return False
    
    def add_hub(self, hub):
        """Add a hub to the network"""
        if hub not in self.hubs:
            self.hubs.append(hub)
            return True
        return False

    def connect(self, entity1, entity2):
        """Connect two entities in the network"""
        entity1_connected = entity1.connect(entity2)
        entity2_connected = entity2.connect(entity1)
        
        if entity1_connected and entity2_connected:
            print(f"Connected {entity1.id} and {entity2.id}")
            return True, f"Connected {entity1.id} and {entity2.id}"
        else:
            return False, "Connection failed"
            
    def disconnect(self, entity1, entity2):
        """Disconnect two entities in the network"""
        entity1_disconnected = entity1.disconnect(entity2)
        entity2_disconnected = entity2.disconnect(entity1)
        
        if entity1_disconnected and entity2_disconnected:
            return True, f"Disconnected {entity1.id} and {entity2.id}"
        else:
            return False, "Disconnection failed"