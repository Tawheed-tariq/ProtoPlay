from core.devices import EndDevice, Hub, Switch, Bridge

class Network:
    def __init__(self):
        self.devices = []
        self.hubs = []
        self.switches = []
        self.bridges = []
        
    def add_device(self, device):
        if device not in self.devices:
            self.devices.append(device)
            return True
        return False
    
    def add_hub(self, hub):
        if hub not in self.hubs:
            self.hubs.append(hub)
            return True
        return False
    
    def add_switch(self, switch):
        if switch not in self.switches:
            self.switches.append(switch)
            return True
        return False
    
    def add_bridge(self, bridge):
        if bridge not in self.bridges:
            self.bridges.append(bridge)
            return True
        return False

    def connect(self, entity1, entity2):
        entity1_connected = entity1.connect(entity2)
        entity2_connected = entity2.connect(entity1)
        
        if entity1_connected and entity2_connected:
            print(f"Connected {entity1.id} and {entity2.id}")
            return True, f"Connected {entity1.id} and {entity2.id}"
        else:
            return False, "Connection failed"
            
