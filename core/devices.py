class Entity:
    def __init__(self, id):
        self.id = id
        self.connected_to = []  
        
    def connect(self, entity):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            return True
        return False
    
class EndDevice(Entity):
    def __init__(self, id, mac):
        super().__init__(id)
        self.mac = mac
        self.received_data = []  # Store received data
        
    def send(self, data, destination, layer=1, visited=None):
        if visited is None:
            visited = set()
        visited.add(self)
        if layer == 1:
            if destination in self.connected_to:
                destination.receive(data, self, layer=layer)
                return True
                    
            for entity in self.connected_to:
                if entity not in visited:
                    if isinstance(entity, Hub):
                        return entity.forward(data, self, destination)
                    elif isinstance(entity, EndDevice):
                        return entity.send(data,destination, layer=layer, visited=visited)
            
            return False
            
        elif layer == 2:
            frame = {
                'source_mac': self.mac,
                'dest_mac': destination.mac,
                'data': data
            }
            
            if destination in self.connected_to:
                destination.receive(frame, self, layer=layer)
                return True
            
            for entity in self.connected_to:
                if isinstance(entity, Hub):
                    return entity.forward(frame, self, destination, layer=layer)
                
                elif isinstance(entity, Switch):
                    return entity.forward(frame, self, destination, layer=layer)
                
                elif isinstance(entity, Bridge):
                    return entity.forward(frame, self, destination, layer=layer)
            
            return False
        
        else:
            return False
    
    def receive(self, data, source, layer=1):
        if layer == 1:
            self.received_data.append({
                "data": data,
                "source": source.id
            })
            print(f"Device {self.id} received data: {data} from {source.id}")
            return True
        elif layer == 2:
            destination_mac = data['dest_mac']
            print(f"Device {self.id} received frame: {data} from {source.id}")
            if destination_mac == self.mac:
                self.received_data.append({
                    "data": data['data'],
                    "source": source.id
                })
                return True
            else:
                return False
        else:
            return False
    
    def __str__(self):
        return f"Device(id={self.id}, mac={self.mac})"

class Hub(Entity):
    def __init__(self, id):
        super().__init__(id)
        
    def forward(self, data, source, destination=None, layer=1):
        success = False
        
        for device in self.connected_to:
            if device != source:  
                if isinstance(device, EndDevice):
                    device.receive(data, self, layer=layer)
                    if device == destination:
                        success = True
                elif isinstance(device, Hub) or isinstance(device, Switch) or isinstance(device, Bridge):
                    hub_success = device.forward(data, self, destination, layer=layer)
                    if hub_success and destination is not None:
                        success = True
        
        return success if destination is not None else True
    
    def __str__(self):
        return f"Hub(id={self.id})"

class Switch(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}
        self.port_table = {}
    
    def connect(self, entity):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            self.port_table[entity] = len(self.port_table)
            return True
        return False
        
    def forward(self, frame, source, destination=None, layer=2):
        if layer < 2:
            return False
        destination_mac = frame["dest_mac"]

        self.mac_table[frame["source_mac"]] = self.port_table[source]
        
        if destination_mac in self.mac_table:
            port = self.mac_table[destination_mac]
            destination_device = self.connected_to[port]
            destination_device.receive(frame, source, layer=layer)
            return True
        else:
            success = False
            for device in self.connected_to:
                if device != source:
                    if isinstance(device, Hub):
                        success = device.forward(frame, source, destination)
                    elif isinstance(device, Switch):
                        success = device.forward(frame, source)
                    elif isinstance(device, Bridge):
                        success = device.forward(frame, self, destination, layer=layer)
                    else:
                        device.receive(frame, source, layer=layer)
                        success = True
            return success
    
    def __str__(self):
        return f"Switch(id={self.id})"

class Bridge(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {} 
        self.port_table = {}
    
    def connect(self, entity):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            self.port_table[entity] = len(self.port_table)
            return True
        return False 
    
    def forward(self, frame, source, destination=None, layer=2):
        if layer < 2:
            return False

        destination_mac = frame["dest_mac"]

        self.mac_table[frame["source_mac"]] = self.port_table[source]

        if destination_mac in self.mac_table:
            port = self.mac_table[destination_mac]
            destination_device = self.connected_to[port]
            destination_device.receive(frame, source, layer=layer)
            return True
        else:
            success = False
            for device in self.connected_to:
                if device != source:
                    if isinstance(device, EndDevice):
                        device.receive(frame, source, layer=layer)
                        success = True
                    elif isinstance(device, Switch) or isinstance(device, Hub):
                        success = device.forward(frame, self, destination, layer= layer)
            
            return success

    def __str__(self):
        return f"Bridge(id={self.id})"
