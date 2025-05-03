class Entity:
    def __init__(self, id):
        self.id = id
        self.connected_to = []  
        
    def connect(self, entity):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  # Bidirectional connection
            return True
        return False
    
    def disconnect(self, entity):
        if entity in self.connected_to:
            self.connected_to.remove(entity)
            if self in entity.connected_to:
                entity.connected_to.remove(self)
            return True
        return False
        
    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id})"

class EndDevice(Entity):
    def __init__(self, id, mac, ip_address, subnet_mask="255.255.255.0", default_gateway=None):
        super().__init__(id)
        self.mac = mac
        self.ip = ip_address
        self.subnet_mask = subnet_mask
        self.default_gateway = default_gateway
        self.received_data = []  # Store received data
        self.arp_table = {}  # MAC to IP mapping
        
    def set_gateway(self, gateway_ip):
        self.default_gateway = gateway_ip
    
    def add_to_arp_table(self, ip, mac):
        self.arp_table[ip] = mac
    
    def same_subnet(self, ip_address):
        """Check if the destination IP is in the same subnet"""
        src_parts = self.ip.split('.')
        dst_parts = ip_address.split('.')
        mask_parts = self.subnet_mask.split('.')
        
        for i in range(4):
            if (int(src_parts[i]) & int(mask_parts[i])) != (int(dst_parts[i]) & int(mask_parts[i])):
                return False
        return True
    
    def send(self, data, destination, layer=3, visited=None):
        """Send data to a destination device"""
        if visited is None:
            visited = set()
        
        # Add the ID to visited set
        visited.add(self.id)
        print(f"Device {self.id} sending data to {destination.id} at layer {layer}")
        
        # For Layer 1 sending
        if layer == 1:
            for entity in self.connected_to:
                if entity.id not in visited:
                    if entity == destination:
                        return entity.receive(data, self, layer=layer)
                    elif isinstance(entity, Hub):
                        visited_copy = visited.copy()
                        return entity.forward(data, self, destination, layer=layer, visited=visited_copy)
            return False
        
        # Layer 2 - Data Link layer (uses MAC addresses)
        elif layer == 2:
            frame = {
                'source_mac': self.mac,
                'dest_mac': destination.mac,
                'data': data
            }
            
            if destination in self.connected_to:
                return destination.receive(frame, self, layer=layer)
            
            for entity in self.connected_to:
                if entity.id not in visited:
                    if isinstance(entity, (Hub, Switch, Bridge)):
                        visited_copy = visited.copy()
                        if entity.forward(frame, self, destination, layer=layer, visited=visited_copy):
                            return True
            return False
        
        # Layer 3 - Network layer (uses IP addresses)
        elif layer == 3:
            dest_ip = destination.ip
            
            # Create the IP packet
            packet = {
                'source_ip': self.ip,
                'dest_ip': dest_ip,
                'ttl': 64,  # Time to live
                'data': data
            }

            print(f"Packet created: src={self.ip}, dst={dest_ip}, data={data}")
            
            # Direct connection or same subnet
            if destination in self.connected_to or self.same_subnet(dest_ip):
                # Resolve MAC address (ARP would happen here)
                if dest_ip not in self.arp_table:
                    self.arp_table[dest_ip] = destination.mac
                
                # Create L2 frame with the resolved MAC
                frame = {
                    'source_mac': self.mac,
                    'dest_mac': self.arp_table[dest_ip],
                    'type': 'IPv4',
                    'data': packet
                }
                
                if destination in self.connected_to:
                    return destination.receive(frame, self, layer=2)
                
                # Send to connected devices that might reach the destination
                for entity in self.connected_to:
                    if entity.id not in visited:
                        if isinstance(entity, (Switch, Bridge, Hub)):
                            visited_copy = visited.copy()
                            if entity.forward(frame, self, destination, layer=2, visited=visited_copy):
                                return True
            
            # Different subnet - need to use gateway
            elif self.default_gateway:
                print(f"Device {self.id}: Sending to gateway {self.default_gateway}")
                
                gateway_mac = None
                gateway_device = None
                
                # Find the gateway device
                for entity in self.connected_to:
                    if isinstance(entity, Router) and entity.has_ip(self.default_gateway):
                        gateway_mac = entity.get_mac_for_interface(self.default_gateway)
                        gateway_device = entity
                        break
                    elif isinstance(entity, (Hub, Switch, Bridge)):
                        # Check if this intermediary network device can reach the gateway
                        for connected_entity in entity.connected_to:
                            print(f"Checking connected entity {connected_entity} for gateway {self.default_gateway}")
                            if isinstance(connected_entity, Router) and connected_entity.has_ip(self.default_gateway):
                                gateway_mac = connected_entity.get_mac_for_interface(self.default_gateway)
                                print(f"received mac addess of gateway: {gateway_mac}")
                                gateway_device = connected_entity
                                break
                        
                        if gateway_mac:
                            break
                
                if gateway_mac and gateway_device:
                    # Create L2 frame with the router's MAC as destination
                    frame = {
                        'source_mac': self.mac,
                        'dest_mac': gateway_mac,
                        'type': 'IPv4',
                        'data': packet
                    }
                    print(f"Device {self.id}: Sending {frame} to gateway {gateway_device.id}")
                    # If directly connected to router
                    if gateway_device in self.connected_to:
                        return gateway_device.receive(frame, self, layer=2)
                    
                    # If connected through another device
                    for entity in self.connected_to:
                        if entity.id not in visited and isinstance(entity, (Hub, Switch, Bridge)):
                            visited_copy = visited.copy()
                            if entity.forward(frame, self, gateway_device, layer=2, visited=visited_copy):
                                return True
                
                print(f"Device {self.id}: Gateway {self.default_gateway} not reachable!")
                return False
            else:
                print(f"Device {self.id}: No gateway configured for destination {dest_ip}!")
                return False
        
        return False
    
    def receive(self, data, source, layer=1):
        """Process received data at different layers"""
        print(f"Device {self.id} received data from {source.id} at layer {layer}")
        
        # Layer 1 - Physical layer (raw bits)
        if layer == 1:
            self.received_data.append({
                "layer": 1,
                "data": data,
                "source": source.id
            })
            print(f"Device {self.id} received raw data from {source.id}")
            return True
            
        # Layer 2 - Data Link layer (MAC addressing)
        elif layer == 2:
            if 'dest_mac' in data:  # It's a frame
                destination_mac = data['dest_mac']
                source_mac = data['source_mac']
                
                print(f"Device {self.id} received frame: src={source_mac}, dst={destination_mac}")
                
                # Update ARP table if IP info is present
                if 'data' in data and isinstance(data['data'], dict) and 'source_ip' in data['data']:
                    self.arp_table[data['data']['source_ip']] = source_mac
                
                # Check if the frame is intended for this device
                if destination_mac == self.mac or destination_mac == "FF:FF:FF:FF:FF:FF":  # Unicast or broadcast
                    # If it's an IPv4 packet, process at layer 3
                    if 'type' in data and data['type'] == 'IPv4':
                        return self.receive(data['data'], source, layer=3)
                    else:
                        self.received_data.append({
                            "layer": 2,
                            "frame": data,
                            "source": source.id
                        })
                        return True
                else:
                    return False  # Not for this device
            return False
            
        # Layer 3 - Network layer (IP addressing)
        elif layer == 3:
            if 'dest_ip' in data:  # It's an IP packet
                destination_ip = data['dest_ip']
                
                # Check if packet is intended for this device
                if destination_ip == self.ip:
                    self.received_data.append({
                        "layer": 3,
                        "packet": data,
                        "source": source.id
                    })
                    print(f"Device {self.id} received IP packet from {data['source_ip']}, data: {data['data']}")
                    return True
                else:
                    return False  # Not for this device
            return False
        
        return False
    
    def __str__(self):
        return f"Device(id={self.id}, mac={self.mac}, ip={self.ip})"

class Hub(Entity):
    def __init__(self, id):
        super().__init__(id)
        
    def forward(self, data, source, destination=None, layer=1, visited=None):
        """Hubs operate at layer 1 and forward all data to all ports except the source"""
        if visited is None:
            visited = set()
            
        # Add self ID to visited
        visited.add(self.id)
        print(f"Hub {self.id} forwarding data from {source.id}")
        
        success = False
        
        for device in self.connected_to:
            # Skip the source device and visited devices
            if device == source or device.id in visited:
                continue
            
            print(f"Hub {self.id} forwarding data to {device.id}")
            
            if isinstance(device, EndDevice):
                result = device.receive(data, self, layer=layer)
                if device == destination and result:
                    success = True
            elif isinstance(device, (Hub, Switch, Bridge, Router)):
                visited_copy = visited.copy()
                result = device.forward(data, self, destination, layer=layer, visited=visited_copy)
                if destination is not None and result:
                    success = True
                
        return success if destination is not None else True

class Switch(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}  # MAC address → port mapping
        self.port_table = {}  # Entity → port number mapping
        self.vlan_table = {}  # Port → VLAN mapping
        self.default_vlan = 1
    
    def connect(self, entity, port=None, vlan=None):
        """Connect a device to a specific port with optional VLAN assignment"""
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  # Bidirectional connection
            
            # Assign port number
            if port is None:
                port = len(self.port_table)
            self.port_table[entity] = port
            
            # Assign VLAN
            if vlan is not None:
                self.vlan_table[port] = vlan
            else:
                self.vlan_table[port] = self.default_vlan
                
            return True
        return False
    
    def set_port_vlan(self, entity, vlan):
        print(f"\n\n\nport table: {self.port_table.items()}")
        """Set VLAN for a specific port"""
        if entity in self.port_table:
            port = self.port_table[entity]
            self.vlan_table[port] = vlan
            return True
        return False
        
    def forward(self, frame, source, destination=None, layer=2, visited=None):
        """Switches operate at layer 2 and use MAC address tables for forwarding"""
        if visited is None:
            visited = set()
            
        # Add self ID to visited
        visited.add(self.id)
        
        # Layer 1 data - forward like a hub
        if layer < 2:
            return self._flood(frame, source, destination, visited)
            
        print(f"Switch {self.id} forwarding frame from {source.id} to {destination.id if destination else 'broadcast'}")
        
        # Update MAC table with source address
        if 'source_mac' in frame:
            source_mac = frame["source_mac"]
            source_port = self.port_table.get(source)
            
            if source_port is not None:
                self.mac_table[source_mac] = source_port
                source_vlan = self.vlan_table.get(source_port, self.default_vlan)
            else:
                source_vlan = self.default_vlan
            
            destination_mac = frame["dest_mac"]
            
            # Broadcast frame
            if destination_mac == "FF:FF:FF:FF:FF:FF":
                return self._flood_vlan(frame, source, destination, source_vlan, visited)
            
            # Unicast frame - check if destination MAC is in our table
            if destination_mac in self.mac_table:
                print(f"Switch {self.id} found destination MAC {destination_mac} in table")
                dest_port = self.mac_table[destination_mac]
                dest_vlan = self.vlan_table.get(dest_port, self.default_vlan)
                
                # Check if both ports are in the same VLAN
                if source_port is not None and dest_vlan == source_vlan:
                    # Find the device connected to this port
                    for device, port in self.port_table.items():
                        if port == dest_port:
                            if device == destination or destination is None:
                                result = device.receive(frame, self, layer=layer)
                                return result
                            elif isinstance(device, (Hub, Switch, Bridge, Router)) and device.id not in visited:
                                visited_copy = visited.copy()
                                return device.forward(frame, self, destination, layer=layer, visited=visited_copy)
            
            # Unknown destination or different VLAN - flood within the same VLAN
            return self._flood_vlan(frame, source, destination, source_vlan, visited)
        else:
            # Handle data without MAC addresses (shouldn't normally happen)
            return self._flood(frame, source, destination, visited)
    
    def _flood(self, data, source, destination=None, visited=None):
        """Send data to all ports except the source port"""
        if visited is None:
            visited = set()
            
        success = False
        for device in self.connected_to:
            if device != source and device.id not in visited:
                if isinstance(device, EndDevice):
                    result = device.receive(data, self, layer=2)
                    if device == destination and result:
                        return True
                    success = success or result
                elif isinstance(device, (Hub, Switch, Bridge, Router)):
                    visited_copy = visited.copy()
                    result = device.forward(data, self, destination, layer=2, visited=visited_copy)
                    if destination is not None and result:
                        return True
                    success = success or result
        return success
    
    def _flood_vlan(self, data, source, destination, source_vlan, visited=None):
        """Send data to all ports in the same VLAN except the source port"""
        if visited is None:
            visited = set()
            
        success = False
        source_port = self.port_table.get(source)
        print(f"Switch {self.id} flooding data in VLAN {source_vlan}")
        
        for device in self.connected_to:
            if device != source and device.id not in visited:
                port = self.port_table.get(device)
                if port is not None:
                    port_vlan = self.vlan_table.get(port, self.default_vlan)
                    if port_vlan == source_vlan:
                        if isinstance(device, EndDevice):
                            result = device.receive(data, self, layer=2)
                            if device == destination and result:
                                return True
                            success = success or result
                        elif isinstance(device, (Hub, Switch, Bridge, Router)):
                            visited_copy = visited.copy()
                            result = device.forward(data, self, destination, layer=2, visited=visited_copy)
                            if destination is not None and result:
                                return True
                            success = success or result
        return success
    
    def get_mac_for_interface(self, ip_address):
        """Get MAC address for the interface with the given IP"""
        for device in self.connected_to:
            if isinstance(device, EndDevice) and device.ip == ip_address:
                return device.mac
            elif isinstance(device, Router):
                mac = device.get_mac_for_interface(ip_address)
                if mac:
                    return mac
        return None
    
    def _is_in_subnet(self, ip, subnet_ip, subnet_mask):
        """Check if IP is in the subnet defined by subnet_ip and subnet_mask"""
        ip_parts = ip.split('.')
        subnet_parts = subnet_ip.split('.')
        mask_parts = subnet_mask.split('.')
        
        for i in range(4):
            if (int(ip_parts[i]) & int(mask_parts[i])) != (int(subnet_parts[i]) & int(mask_parts[i])):
                return False
        return True

class Bridge(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}  # MAC address → port mapping
        self.port_table = {}  # Entity → port number mapping
    
    def connect(self, entity, port=None):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  # Bidirectional connection
            
            # Assign port number
            if port is None:
                port = len(self.port_table)
            self.port_table[entity] = port
            return True
        return False 
    
    def forward(self, frame, source, destination=None, layer=2, visited=None):
        """Bridges operate at layer 2 and separate collision domains"""
        if visited is None:
            visited = set()
            
        # Add self ID to visited
        visited.add(self.id)
        
        if layer < 2:
            return False  # Bridges don't forward layer 1 data

        # Update MAC table with source address
        if 'source_mac' in frame:
            source_mac = frame["source_mac"]
            source_port = self.port_table.get(source)
            
            if source_port is not None:
                self.mac_table[source_mac] = source_port
            
            destination_mac = frame["dest_mac"]
            
            # Broadcast frame
            if destination_mac == "FF:FF:FF:FF:FF:FF":
                return self._flood(frame, source, destination, visited)
            
            # Unicast frame - check if destination MAC is in our table
            if destination_mac in self.mac_table:
                dest_port = self.mac_table[destination_mac]
                
                # Find the device connected to this port
                for device, port in self.port_table.items():
                    if port == dest_port:
                        if device == destination or destination is None:
                            return device.receive(frame, self, layer=layer)
                        elif isinstance(device, (Hub, Switch, Bridge, Router)) and device.id not in visited:
                            visited_copy = visited.copy()
                            return device.forward(frame, self, destination, layer=layer, visited=visited_copy)
            
            # Unknown destination - flood
            return self._flood(frame, source, destination, visited)
        else:
            # Handle data without MAC addresses (shouldn't normally happen)
            return self._flood(frame, source, destination, visited)
    
    def _flood(self, data, source, destination=None, visited=None):
        """Send data to all ports except the source port"""
        if visited is None:
            visited = set()
            
        success = False
        for device in self.connected_to:
            if device != source and device.id not in visited:
                if isinstance(device, EndDevice):
                    result = device.receive(data, self, layer=2)
                    if device == destination and result:
                        return True
                    success = success or result
                elif isinstance(device, (Hub, Switch, Bridge, Router)):
                    visited_copy = visited.copy()
                    result = device.forward(data, self, destination, layer=2, visited=visited_copy)
                    if destination is not None and result:
                        return True
                    success = success or result
        return success

class Router(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.interfaces = {}  # Interface name → {ip, mac, subnet} 
        self.routing_table = []  # [{network, subnet_mask, next_hop, interface}, ...]
        self.port_table = {}  # Entity → interface mapping
        self.arp_table = {}  # IP → MAC mapping
        self.nat_table = {}  # For NAT functionality
        self.public_ip = None  # For internet connectivity
    
    def add_interface(self, name, ip_address, mac_address, subnet_mask="255.255.255.0"):
        """Add a network interface to the router"""
        self.interfaces[name] = {
            'ip': ip_address,
            'mac': mac_address,
            'subnet_mask': subnet_mask
        }
        
        # Add a direct route for this network
        network = self._get_network(ip_address, subnet_mask)
        self.add_route(network, subnet_mask, None, name)
        
        return True
    
    def _get_network(self, ip, subnet_mask):
        """Calculate network address from IP and subnet mask"""
        ip_parts = ip.split('.')
        mask_parts = subnet_mask.split('.')
        network_parts = []
        
        for i in range(4):
            network_parts.append(str(int(ip_parts[i]) & int(mask_parts[i])))
        
        return '.'.join(network_parts)
    
    def has_ip(self, ip_address):
        """Check if the router has the given IP on any interface"""
        print(f"Router {self.id} checking for IP {ip_address} in {self.interfaces.items()}")
        for interface, details in self.interfaces.items():
            print(f"Checking interface {interface}: {details}")
            if details['ip'] == ip_address:
                return True
        return False
    
    def get_mac_for_interface(self, ip_address):
        """Get MAC address for the interface with the given IP"""
        for interface, details in self.interfaces.items():
            if details['ip'] == ip_address:
                return details['mac']
        return None
    
    def get_interface_for_ip(self, ip_address):
        # First check direct match
        for interface, details in self.interfaces.items():
            if details['ip'] == ip_address:
                return interface
                
        # If no direct match, check subnet matches
        for interface, details in self.interfaces.items():
            if self._is_in_subnet(ip_address, details['ip'], details['subnet_mask']):
                return interface
                
        return None
    
    def _is_in_subnet(self, ip, subnet_ip, subnet_mask):
        """Check if IP is in the subnet defined by subnet_ip and subnet_mask"""
        ip_parts = ip.split('.')
        subnet_parts = subnet_ip.split('.')
        mask_parts = subnet_mask.split('.')
        
        for i in range(4):
            if (int(ip_parts[i]) & int(mask_parts[i])) != (int(subnet_parts[i]) & int(mask_parts[i])):
                return False
        return True
    
    def connect(self, entity, interface_name):
        """Connect a device to a specific interface"""
        if entity not in self.connected_to and interface_name in self.interfaces:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  # Bidirectional connection
            self.port_table[entity] = interface_name
            
            # If it's an EndDevice, set its gateway to this interface's IP
            if isinstance(entity, EndDevice):
                entity.set_gateway(self.interfaces[interface_name]['ip'])
                
            return True
        return False
    
    def add_route(self, network, subnet_mask, next_hop, interface):
        """Add a route to the routing table"""
        self.routing_table.append({
            'network': network,
            'subnet_mask': subnet_mask,
            'next_hop': next_hop,  # None for directly connected networks
            'interface': interface
        })
        return True
    
    def add_default_route(self, next_hop, interface):
        """Add a default route (0.0.0.0/0)"""
        return self.add_route("0.0.0.0", "0.0.0.0", next_hop, interface)
    
    def set_public_ip(self, public_ip):
        """Set public IP for NAT functionality"""
        self.public_ip = public_ip
        return True
    
    def enable_nat(self):
        """Enable Network Address Translation"""
        if not self.public_ip:
            print("Cannot enable NAT without a public IP address")
            return False
        return True
    
    def _match_route(self, dest_ip):
        """Find the best matching route for a destination IP"""
        best_match = None
        best_mask_count = -1
        
        for route in self.routing_table:
            # Check if this route matches the destination
            print(f"Matching route: {route} with destination {dest_ip}")
            ip_parts = dest_ip.split('.')
            net_parts = route['network'].split('.')
            mask_parts = route['subnet_mask'].split('.')
            
            matches = True
            mask_bit_count = 0
            
            for i in range(4):
                mask_int = int(mask_parts[i])
                mask_bit_count += bin(mask_int).count('1')
                
                if mask_int == 0:  # This octet doesn't matter
                    continue
                
                if (int(ip_parts[i]) & mask_int) != int(net_parts[i]):
                    matches = False
                    break
            
            if matches and mask_bit_count > best_mask_count:
                best_match = route
                best_mask_count = mask_bit_count
        
        return best_match
    
    def forward(self, packet, source, destination=None, layer=3, visited=None):
        """Route packets based on destination IP and routing table"""
        if visited is None:
            visited = set()
            
        # Add self ID to visited
        visited.add(self.id)
        
        # For layer 2 frames
        if layer == 2 and isinstance(packet, dict) and 'type' in packet and packet['type'] == 'IPv4':
            return self.receive(packet, source, layer)
        
        # For layer 3 packets
        if layer == 3 and isinstance(packet, dict) and 'dest_ip' in packet:
            print(f"\nRouter {self.id} processing packet: {packet} at layer {layer}\n")
            dest_ip = packet['dest_ip']
            
            # Decrement TTL
            packet['ttl'] = packet.get('ttl', 64) - 1
            if packet['ttl'] <= 0:
                print(f"Router {self.id}: TTL expired for packet to {dest_ip}")
                return False
            
            # Find the best matching route
            route = self._match_route(dest_ip)
            print(f"route received: {route}")
            
            if route:
                outgoing_interface = route['interface']
                next_hop = route['next_hop']
                
                # If no next hop specified, the destination is directly connected
                if not next_hop:
                    # Try to find directly connected device with matching IP
                    print(f"\n\nRouter {self.id}: port table: {self.port_table.items()}\n\n")
                    for device, interface in self.port_table.items():
                        if interface == outgoing_interface:
                            if isinstance(device, EndDevice) and device.ip == dest_ip:
                                # Create frame for the destination
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': device.mac,
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                return device.receive(frame, self, layer=2)
                            elif isinstance(device, (Switch, Hub, Bridge)) and device.id not in visited:
                                # Send to connected network device, letting it find the destination
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': "FF:FF:FF:FF:FF:FF",  # Use broadcast for MAC discovery
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                visited_copy = visited.copy()
                                return device.forward(frame, self, destination, layer=2, visited=visited_copy)
                
                # Forward to the next hop router
                else:
                    # Find the next hop device
                    next_hop_device = None
                    next_hop_mac = None
                    
                    # First check direct connections
                    for device, interface in self.port_table.items():
                        if interface == outgoing_interface:
                            if isinstance(device, Router):
                                for intf_name, intf_details in device.interfaces.items():
                                    if intf_details['ip'] == next_hop:
                                        next_hop_device = device
                                        next_hop_mac = intf_details['mac']
                                        break
                            elif isinstance(device, (Switch, Hub, Bridge)) and device.id not in visited:
                                # Create frame for next hop with broadcast MAC initially
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': "FF:FF:FF:FF:FF:FF",  # Will try ARP-like resolution
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                
                                # Check if the device can help us find the next hop MAC
                                next_hop_mac = device.get_mac_for_interface(next_hop)
                                if next_hop_mac:
                                    frame['dest_mac'] = next_hop_mac
                                
                                # Forward through the connected network device
                                visited_copy = visited.copy()
                                return device.forward(frame, self, None, layer=2, visited=visited_copy)
                    
                    # If we have a direct connection to the next hop router
                    if next_hop_device and next_hop_mac:
                        # Create frame for the next hop router
                        frame = {
                            'source_mac': self.interfaces[outgoing_interface]['mac'],
                            'dest_mac': next_hop_mac,
                            'type': 'IPv4',
                            'data': packet
                        }
                        
                        return next_hop_device.receive(frame, self, layer=2)
            
            # No route found
            print(f"Router {self.id}: No route to {dest_ip}")
            return False
            
        return False
    
    def receive(self, frame, source, layer=2):
        """Process incoming frames/packets"""
        # Layer 2 processing
        if layer == 2 and isinstance(frame, dict) and 'type' in frame and frame['type'] == 'IPv4':
            # Extract the packet
            packet = frame['data']
            dest_ip = packet['dest_ip']
            
            # Check if packet is destined for one of our interfaces
            for interface_name, interface in self.interfaces.items():
                if packet['dest_ip'] == interface['ip']:
                    # Packet for the router itself
                    print(f"Router {self.id}: Received packet for interface {interface_name}")
                    return True
            
            # Forward the packet
            return self.forward(packet, source, layer=3)
        
        return False
