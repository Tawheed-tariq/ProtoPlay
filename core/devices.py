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
        
    def send(self, data, destination, layer=1, visited=None):
        """
        Send data to a destination device at the specified layer
        
        Parameters:
        data - The data to send
        destination - The target device to receive the data
        layer - Integer representing the network layer (1=Physical, 2=Data Link)
        
        Returns:
        Boolean indicating success or failure
        """
        if visited is None:
            visited = set()
        visited.add(self)
        # Layer 1: Physical Layer (bits transmission)
        if layer == 1:
            # At physical layer, we just send bits
            # Check if we're directly connected to the destination
            if destination in self.connected_to:
                destination.receive(data, self, layer=layer)
                return True
                    
            # If not directly connected, check if we're connected to a hub
            for entity in self.connected_to:
                if entity not in visited:
                    if isinstance(entity, Hub):
                        # Forward through the hub
                        return entity.forward(data, self, destination)
                    elif isinstance(entity, EndDevice):
                        # Not connected to a hub, send directly to the device
                        return entity.send(data,destination, layer=layer, visited=visited)
            
            return False
            
        # Layer 2: Data Link Layer (frames with MAC addresses)
        elif layer == 2:
            # At data link layer, we use MAC addresses for addressing
            frame = {
                'source_mac': self.mac,
                'dest_mac': destination.mac,
                'data': data
            }
            
            # Check if we're directly connected to the destination
            if destination in self.connected_to:
                destination.receive(frame, self, layer=layer)
                return True
            
            # If not directly connected, try sending through connected devices
            for entity in self.connected_to:
                # If connected to a hub, it will broadcast at physical layer
                if isinstance(entity, Hub):
                    return entity.forward(frame, self, destination)
                
                # If connected to a switch, it will use MAC addresses for forwarding
                elif isinstance(entity, Switch):
                    return entity.forward(frame, self, destination, layer=layer)
            
            return False
        
        # Future expansion: Layer 3+ (Network Layer and above)
        else:
            # Higher layer handling would go here
            # For example, Layer 3 would use IP addresses instead of MAC addresses
            # This is a placeholder for future expansion
            return False
    
    def receive(self, data, source, layer=1):
        """Receive data from a source device"""
        if layer == 1:
            self.received_data.append({
                "data": data,
                "source": source.id
            })
            print(f"Device {self.id} received data: {data} from {source.id}")
            return True
        elif layer == 2:
            # At data link layer, we receive frames with MAC addresses
            destination_mac = data['dest_mac']
            if destination_mac == self.mac:
                self.received_data.append({
                    "data": data['data'],
                    "source": source.id
                })
                print(f"Device {self.id} received frame: {data} from {source.id}")
                return True
            else:
                return False
        else:
            # Higher layer handling would go here
            # This is a placeholder for future expansion
            return False
    
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
                    hub_success = device.forward(data, self, destination)
                    if hub_success and destination is not None:
                        success = True
        
        return success if destination is not None else True
    
    def __str__(self):
        return f"Hub(id={self.id})"

class Switch(Entity):
    """Represents a switch in the network that forwards frames based on MAC addresses"""
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}  # MAC address to port mapping
        
    def forward(self, frame, source, destination=None, layer=2):
        """
        Forward frames based on MAC addresses
        """
        # Layer 2: Data Link Layer (frames with MAC addresses)
        if layer < 2:
            return False
        destination_mac = frame["dest_mac"]

        # Learn the source MAC address
        self.mac_table[frame["source_mac"]] = source
        
        # If the destination MAC is in the MAC table, forward to the correct port
        if destination_mac in self.mac_table:
            destination_device = self.mac_table[destination_mac]
            destination_device.receive(frame, source, layer=layer)
            return True
        else:
            # Flood the frame to all ports except the source port
            success = False
            for device in self.connected_to:
                if device != source:
                    print(device)
                    if isinstance(device, Hub):
                        # Hubs broadcast to all connected devices
                        success = device.forward(frame, source, destination)
                    elif isinstance(device, Switch):
                        # Switches forward to all connected devices
                        success = device.forward(frame, source)
                    else:
                        print(device)
                        device.receive(frame, source, layer=layer)
                        success = True
            return success
    
    def __str__(self):
        return f"Switch(id={self.id})"

class Bridge(Entity):
    """Represents a bridge in the network that filters and forwards frames between network segments"""
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}  # MAC address to port mapping
    
    def forward(self, frame, source, destination=None, layer=2):
        """
        Forward frames based on MAC addresses, filtering traffic between segments
        """
        if layer < 2:
            return False

        destination_mac = frame["dest_mac"]

        # Learn the source MAC address and associate it with the source port
        self.mac_table[frame["source_mac"]] = source

        # If the destination MAC is known, forward only to the correct port
        if destination_mac in self.mac_table:
            destination_device = self.mac_table[destination_mac]
            destination_device.receive(frame, source, layer=layer)
            return True
        else:
            # Flood the frame only to the other segment
            success = False
            for device in self.connected_to:
                if device != source:
                    if isinstance(device, EndDevice):
                        device.receive(frame, source, layer=layer)
                        success = True
                    elif isinstance(device, Switch) or isinstance(device, Hub):
                        success = device.forward(frame, source, destination)
            
            return success

    def __str__(self):
        return f"Bridge(id={self.id})"
