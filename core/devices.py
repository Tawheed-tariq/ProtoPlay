import random
from collections import defaultdict
import time
import streamlit as st
import os

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
            
    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id})"

class EndDevice(Entity):
    def __init__(self, id, mac, ip_address, subnet_mask="255.255.255.0", default_gateway=None):
        super().__init__(id)
        self.mac = mac
        self.ip = ip_address
        self.subnet_mask = subnet_mask
        self.default_gateway = default_gateway
        self.received_data = []  
        self.arp_table = {}  
        self.ports = {}  # port_num -> {"protocol", "service", "handler"}
        self.connections = defaultdict(dict)  # (ip, port) -> connection state
        
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
    
    def assign_port(self, port_num, protocol, service_name, handler=None):
        """Assign a well-known port to a service"""
        if port_num in self.ports:
            return False
        
        self.ports[port_num] = {
            "protocol": protocol,
            "service": service_name,
            "handler": handler
        }
        return True
    
    def send(self, data, destination, layer=3, visited=None):
        if visited is None:
            visited = set()
        
        visited.add(self.id)
        
        if layer == 1:
            for entity in self.connected_to:
                if entity.id not in visited:
                    if entity == destination:
                        return entity.receive(data, self, layer=layer)
                    elif isinstance(entity, Hub):
                        visited_copy = visited.copy()
                        return entity.forward(data, self, destination, layer=layer, visited=visited_copy)
            return False
        
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
        
        elif layer == 3:
            print(f"Sending data to {destination.ip} at layer 3")
            dest_ip = destination.ip
            
            packet = {
                'source_ip': self.ip,
                'dest_ip': dest_ip,
                'ttl': 64, 
                'data': data
            }

            print(f"Packet to send: {packet}")

            if destination in self.connected_to or self.same_subnet(dest_ip):
                print(f"Destination {dest_ip} is present in same subnet or directly connected.")
                if dest_ip not in self.arp_table:
                    self.arp_table[dest_ip] = destination.mac
                
                frame = {
                    'source_mac': self.mac,
                    'dest_mac': self.arp_table[dest_ip],
                    'type': 'IPv4',
                    'data': packet
                }

                print(f"Frame to send: {frame}")
                
                if destination in self.connected_to:
                    return destination.receive(frame, self, layer=2)
                
                for entity in self.connected_to:
                    if entity.id not in visited:
                        if isinstance(entity, (Switch, Bridge, Hub)):
                            visited_copy = visited.copy()
                            if entity.forward(frame, self, destination, layer=2, visited=visited_copy):
                                return True
            
            elif self.default_gateway:
                gateway_mac = None
                gateway_device = None
                
                for entity in self.connected_to:
                    if isinstance(entity, Router) and entity.has_ip(self.default_gateway):
                        gateway_mac = entity.get_mac_for_interface(self.default_gateway)
                        gateway_device = entity
                        break
                    elif isinstance(entity, (Hub, Switch, Bridge)):
                        for connected_entity in entity.connected_to:
                            if isinstance(connected_entity, Router) and connected_entity.has_ip(self.default_gateway):
                                gateway_mac = connected_entity.get_mac_for_interface(self.default_gateway)
                                gateway_device = connected_entity
                                break
                        
                        if gateway_mac:
                            break
                
                if gateway_mac and gateway_device:
                    print(f"Gateway found: {gateway_device.id} with MAC {gateway_mac}")
                    frame = {
                        'source_mac': self.mac,
                        'dest_mac': gateway_mac,
                        'type': 'IPv4',
                        'data': packet
                    }

                    print(f"Frame to send to gateway: {frame}")
                    
                    if gateway_device in self.connected_to:
                        return gateway_device.receive(frame, self, layer=2)
                    
                    for entity in self.connected_to:
                        if entity.id not in visited and isinstance(entity, (Hub, Switch, Bridge)):
                            visited_copy = visited.copy()
                            if entity.forward(frame, self, gateway_device, layer=2, visited=visited_copy):
                                return True
                
                return False
            else:
                return False
        
        return False
    
    def receive(self, data, source, layer=1):
        print(f"Device {self.id} receiving data from {source.id}")
        print(f"Data: {data}")
        if layer == 1:
            self.received_data.append({
                "layer": 1,
                "data": data,
                "source": source.id
            })
            return True
            
        elif layer == 2:
            if 'dest_mac' in data:  
                destination_mac = data['dest_mac']
                source_mac = data['source_mac']
                
                if 'data' in data and isinstance(data['data'], dict) and 'source_ip' in data['data']:
                    self.arp_table[data['data']['source_ip']] = source_mac
                
                if destination_mac == self.mac or destination_mac == "FF:FF:FF:FF:FF:FF": 
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
                    return False  
            return False
            
        elif layer == 3:
            if 'dest_ip' in data:  
                destination_ip = data['dest_ip']
                
                if destination_ip == self.ip:
                    self.received_data.append({
                        "layer": 3,
                        "packet": data,
                        "source": source.id
                    })
                    
                    if isinstance(data['data'], str) and ('HTTP' in data['data'] or 'GET' in data['data'] or 'DNS' in data['data']):
                        src_port = dest_port = None
                        if 'source_port' in data:
                            src_port = data['source_port']
                        if 'dest_port' in data:
                            dest_port = data['dest_port']
                            
                        self.received_data.append({
                            "layer": 4,
                            "data": data['data'],
                            "source": source.id,
                            "source_port": src_port,
                            "dest_port": dest_port,
                            "protocol": "tcp" if 'TCP' in data['data'] else "udp"
                        })
                    return True
                else:
                    return False  
            return False
        
        return False
    
    def __str__(self):
        return f"Device(id={self.id}, mac={self.mac}, ip={self.ip})"

class Hub(Entity):
    def __init__(self, id):
        super().__init__(id)
        
    def forward(self, data, source, destination=None, layer=1, visited=None):
        if visited is None:
            visited = set()
        print(f"Hub {self.id} broadcasting data from {source.id} to {destination.id if destination else ""}")
        visited.add(self.id)
        
        success = False
        
        for device in self.connected_to:
            if device == source or device.id in visited:
                continue
            
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
        self.mac_table = {}  
        self.port_table = {}  
        self.vlan_table = {}  
        self.default_vlan = 1
    
    def connect(self, entity, port=None, vlan=None):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  
            
            if port is None:
                port = len(self.port_table)
            self.port_table[entity] = port
            
            if vlan is not None:
                self.vlan_table[port] = vlan
            else:
                self.vlan_table[port] = self.default_vlan
                
            return True
        return False
    
    def set_port_vlan(self, entity, vlan):
        if entity in self.port_table:
            port = self.port_table[entity]
            self.vlan_table[port] = vlan
            return True
        return False
        
    def forward(self, frame, source, destination=None, layer=2, visited=None):
        if visited is None:
            visited = set()
        print(f"Switch {self.id} forwarding frame from {source.id}")
        visited.add(self.id)
        
        if layer < 2:
            return self._flood(frame, source, destination, visited)
            
        if 'source_mac' in frame:
            source_mac = frame["source_mac"]
            source_port = self.port_table.get(source)
            
            if source_port is not None:
                self.mac_table[source_mac] = source_port
                source_vlan = self.vlan_table.get(source_port, self.default_vlan)
            else:
                source_vlan = self.default_vlan
            
            destination_mac = frame["dest_mac"]
            
            if destination_mac == "FF:FF:FF:FF:FF:FF":
                return self._flood_vlan(frame, source, destination, source_vlan, visited)
            
            if destination_mac in self.mac_table:
                dest_port = self.mac_table[destination_mac]
                dest_vlan = self.vlan_table.get(dest_port, self.default_vlan)
                print(f"Destination MAC {destination_mac} found on port {dest_port}")
                if source_port is not None and dest_vlan == source_vlan:
                    for device, port in self.port_table.items():
                        if port == dest_port:
                            if device == destination or destination is None:
                                print(f"Sending frame to {device.id} on port {port}")
                                result = device.receive(frame, self, layer=layer)
                                return result
                            elif isinstance(device, (Hub, Switch, Bridge, Router)) and device.id not in visited:
                                print(f"Forwarding frame to {device.id} on port {port}")
                                visited_copy = visited.copy()
                                return device.forward(frame, self, destination, layer=layer, visited=visited_copy)
            
            return self._flood_vlan(frame, source, destination, source_vlan, visited)
        else:
            return self._flood(frame, source, destination, visited)
    
    def _flood(self, data, source, destination=None, visited=None):
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
        if visited is None:
            visited = set()
            
        success = False
        source_port = self.port_table.get(source)
        
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
        print(f"Switch {self.id} looking for MAC Address of IP {ip_address}")
        for device in self.connected_to:
            if isinstance(device, EndDevice) and device.ip == ip_address:
                return device.mac
            elif isinstance(device, Router):
                mac = device.get_mac_for_interface(ip_address)
                if mac:
                    return mac
        return None

class Bridge(Entity):
    def __init__(self, id):
        super().__init__(id)
        self.mac_table = {}  
        self.port_table = {}  
    
    def connect(self, entity, port=None):
        if entity not in self.connected_to:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  
            
            if port is None:
                port = len(self.port_table)
            self.port_table[entity] = port
            return True
        return False 
    
    def forward(self, frame, source, destination=None, layer=2, visited=None):
        """Bridges operate at layer 2 and separate collision domains"""
        if visited is None:
            visited = set()
            
        visited.add(self.id)
        
        if layer < 2:
            return False  

        if 'source_mac' in frame:
            source_mac = frame["source_mac"]
            source_port = self.port_table.get(source)
            
            if source_port is not None:
                self.mac_table[source_mac] = source_port
            
            destination_mac = frame["dest_mac"]
            
            if destination_mac == "FF:FF:FF:FF:FF:FF":
                return self._flood(frame, source, destination, visited)
            
            if destination_mac in self.mac_table:
                dest_port = self.mac_table[destination_mac]
                
                for device, port in self.port_table.items():
                    if port == dest_port:
                        if device == destination or destination is None:
                            return device.receive(frame, self, layer=layer)
                        elif isinstance(device, (Hub, Switch, Bridge, Router)) and device.id not in visited:
                            visited_copy = visited.copy()
                            return device.forward(frame, self, destination, layer=layer, visited=visited_copy)
            
            return self._flood(frame, source, destination, visited)
        else:
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
        self.interfaces = {}  # Interface name : {ip, mac, subnet} 
        self.routing_table = []  # [{network, subnet_mask, next_hop, interface}, ...]
        self.port_table = {}  
        self.arp_table = {}  
        self.public_ip = None  
    
    def add_interface(self, name, ip_address, mac_address, subnet_mask="255.255.255.0"):
        self.interfaces[name] = {
            'ip': ip_address,
            'mac': mac_address,
            'subnet_mask': subnet_mask
        }
        
        network = self._get_network(ip_address, subnet_mask)
        self.add_route(network, subnet_mask, None, name)
        
        return True
    
    def _get_network(self, ip, subnet_mask):
        ip_parts = ip.split('.')
        mask_parts = subnet_mask.split('.')
        network_parts = []
        
        for i in range(4):
            network_parts.append(str(int(ip_parts[i]) & int(mask_parts[i])))
        
        return '.'.join(network_parts)
    
    def has_ip(self, ip_address):
        for interface, details in self.interfaces.items():
            if details['ip'] == ip_address:
                return True
        return False
    
    def get_mac_for_interface(self, ip_address):
        print(f"Router {self.id} looking for MAC Address of IP {ip_address}")
        for interface, details in self.interfaces.items():
            if details['ip'] == ip_address:
                return details['mac']
        return None
    
    def get_interface_for_ip(self, ip_address):
        print(f"Router {self.id} looking for interface for IP {ip_address}")
        for interface, details in self.interfaces.items():
            if details['ip'] == ip_address:
                return interface
                
        for interface, details in self.interfaces.items():
            if self._is_in_subnet(ip_address, details['ip'], details['subnet_mask']):
                return interface
                
        return None
    
    def _is_in_subnet(self, ip, subnet_ip, subnet_mask):
        ip_parts = ip.split('.')
        subnet_parts = subnet_ip.split('.')
        mask_parts = subnet_mask.split('.')
        
        for i in range(4):
            if (int(ip_parts[i]) & int(mask_parts[i])) != (int(subnet_parts[i]) & int(mask_parts[i])):
                return False
        return True
    
    def connect(self, entity, interface_name, another_router_interface=None):
        if entity not in self.connected_to and interface_name in self.interfaces:
            self.connected_to.append(entity)
            entity.connected_to.append(self)  
            self.port_table[entity] = interface_name
            if isinstance(entity, Router):
                entity.port_table[self] = another_router_interface
            
            if isinstance(entity, EndDevice):
                entity.set_gateway(self.interfaces[interface_name]['ip'])
                
            return True
        return False
    
    def add_route(self, network, subnet_mask, next_hop, interface):
        self.routing_table.append({
            'network': network,
            'subnet_mask': subnet_mask,
            'next_hop': next_hop,  
            'interface': interface
        })
        return True
    
    def add_default_route(self, next_hop, interface):
        return self.add_route("0.0.0.0", "0.0.0.0", next_hop, interface)
            
    def _match_route(self, dest_ip):
        best_match = None
        best_mask_count = -1
        
        for route in self.routing_table:
            ip_parts = dest_ip.split('.')
            net_parts = route['network'].split('.')
            mask_parts = route['subnet_mask'].split('.')
            
            matches = True
            mask_bit_count = 0
            
            for i in range(4):
                mask_int = int(mask_parts[i])
                mask_bit_count += bin(mask_int).count('1')
                
                if mask_int == 0:  
                    continue
                
                if (int(ip_parts[i]) & mask_int) != int(net_parts[i]):
                    matches = False
                    break
            
            if matches and mask_bit_count > best_mask_count:
                best_match = route
                best_mask_count = mask_bit_count
        
        return best_match
    
    def forward(self, packet, source, destination=None, layer=3, visited=None):
        if visited is None:
            visited = set()
        visited.add(self.id)
        
        if layer == 2 and isinstance(packet, dict) and 'type' in packet and packet['type'] == 'IPv4':
            return self.receive(packet, source, layer)
        
        if layer == 3 and isinstance(packet, dict) and 'dest_ip' in packet:
            dest_ip = packet['dest_ip']
            print(f"Router {self.id} processing packet for destination {dest_ip}")
            packet['ttl'] = packet.get('ttl', 64) - 1
            if packet['ttl'] <= 0:
                return False
            
            route = self._match_route(dest_ip)
            print(f"Best Matched route: {route}")
            if route:
                outgoing_interface = route['interface']
                next_hop = route['next_hop']
                
                if not next_hop:
                    print(f"No next hop for {dest_ip}, sending directly to interface {outgoing_interface}")
                    for device, interface in self.port_table.items():
                        if interface == outgoing_interface:
                            if isinstance(device, EndDevice) and device.ip == dest_ip:
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': device.mac,
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                return device.receive(frame, self, layer=2)
                            elif isinstance(device, (Switch, Hub, Bridge)) and device.id not in visited:
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': "FF:FF:FF:FF:FF:FF",  
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                visited_copy = visited.copy()
                                return device.forward(frame, self, destination, layer=2, visited=visited_copy)
                
                else:
                    next_hop_device = None
                    next_hop_mac = None
                    print(f"Next hop for {dest_ip} is {next_hop} via interface {outgoing_interface}")
                    for device, interface in self.port_table.items():
                        if interface == outgoing_interface:
                            if isinstance(device, Router):
                                for intf_name, intf_details in device.interfaces.items():
                                    if intf_details['ip'] == next_hop:
                                        next_hop_device = device
                                        next_hop_mac = intf_details['mac']
                                        break
                                if next_hop_device:  
                                    break
                            elif isinstance(device, (Switch, Hub, Bridge)) and device.id not in visited:
                                frame = {
                                    'source_mac': self.interfaces[outgoing_interface]['mac'],
                                    'dest_mac': "FF:FF:FF:FF:FF:FF",  # Will try ARP-like resolution
                                    'type': 'IPv4',
                                    'data': packet
                                }
                                next_hop_mac = device.get_mac_for_interface(next_hop)
                                print(f"Next hop MAC for {next_hop} is {next_hop_mac}")
                                if next_hop_mac:
                                    frame['dest_mac'] = next_hop_mac
                                
                                visited_copy = visited.copy()
                                return device.forward(frame, self, destination, layer=2, visited=visited_copy)
                    
                    if next_hop_device and next_hop_mac:
                        frame = {
                            'source_mac': self.interfaces[outgoing_interface]['mac'],
                            'dest_mac': next_hop_mac,
                            'type': 'IPv4',
                            'data': packet
                        }

                        print(f"Sending frame to next hop device {next_hop_device.id} with MAC {next_hop_mac}")
                        
                        return next_hop_device.receive(frame, self, layer=2)
            
            return False
            
        return False
    
    def receive(self, frame, source, layer=2):
        if layer == 2 and isinstance(frame, dict) and 'type' in frame and frame['type'] == 'IPv4':
            packet = frame['data']
            dest_ip = packet['dest_ip']
            
            for interface_name, interface in self.interfaces.items():
                if packet['dest_ip'] == interface['ip']:
                    return True
            
            return self.forward(packet, source, layer=3)
        
        return False

class TransportLayerSimulator:
    def __init__(self):
        self.connections = defaultdict(dict)  # (device_id, ip, port) 
        
    def get_ephemeral_port(self, device):
        used_ports = set(port_num for port_num, port in device.ports.items())
        while True:
            port = random.randint(49152, 65535)
            if port not in used_ports:
                return port
        

    def log_message(self, src, dest, data, src_port=None, dest_port=None, protocol=None):
        msg = {
            "timestamp": time.strftime("%H:%M:%S"),
            "source": src.id,
            "destination": dest.id,
            "data": data,
            "source_port": src_port,
            "dest_port": dest_port,
            "protocol": protocol,
            "layer": 4 if protocol else 5
        }
        
        src.received_data.append(msg)
        dest.received_data.append(msg)
        
        st.session_state.messages.append(msg)

def http_handler(request):
    if "GET /" in request:
        return ("HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                "\r\n"
                "<html><body><h1>Hello Tawheed!</h1></body></html>")
    return None

def dns_handler(query):
    dns_records = {
        "example.com": "192.168.1.100",
        "test.com": "192.168.1.101"
    }
    if query in dns_records:
        return f"DNS Response: {query} -> {dns_records[query]}"
    return f"DNS Response: NXDOMAIN (No record for {query})"

def ftp_handler(command, uploaded_file=None):
    if command..startswith("LIST"):
        try:
            files = os.listdir('.')
            file_list = "\n".join(files) if files else "Directory is empty"
            return f"Opening data connection\n{file_list}\nTransfer complete"
        except Exception as e:
            return "Failed to list"
    elif command.startswith("PUT"):
        if uploaded_file is not None:
            try:
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                first_line = content.split('\n')[0] if content else "Empty file"
                print(f"First line of file recieved: {first_line}")
            except Exception as e:
                print(f"Error reading file: {e}")
            return f"File {uploaded_file} received successfully\nTransfer complete"
        else:
            return f"Error: No file provided for upload"
    return "500 Unknown command"