from core.devices import EndDevice, Hub, Switch
class Network:
    """Represents the entire network"""
    def __init__(self):
        self.devices = []
        self.hubs = []
        self.switches = []
        
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
    
    def add_switch(self, switch):
        """Add a switch to the network"""
        if switch not in self.switches:
            self.switches.append(switch)
            return True
        return

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