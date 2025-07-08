import streamlit as st
from core.devices import EndDevice, Hub, Switch, Bridge, Router, http_handler, dns_handler, ftp_handler, TransportLayerSimulator
from core.network import Network
from collections import defaultdict
import random
import time
from core.functions import visualize_topology, find_path, restore_connections, initialize_session_state
from core.external import prebuilt_network_ui


def add_device():
    with st.form("add_device"):
        st.subheader("Add End Device")
        device_id = st.text_input("Device ID", key="device_id")
        mac_address = st.text_input("MAC Address (format: XX:XX:XX:XX:XX:XX)", key="mac_address")
        ip_address = st.text_input("IP Address (format: X.X.X.X)", key="ip_address")
        subnet_mask = st.text_input("Subnet Mask (format: X.X.X.X)", value="255.255.255.0", key="subnet_mask")
        
        if st.form_submit_button("Add Device"):
            if device_id and mac_address and ip_address:
                if device_id not in st.session_state.devices:
                    new_device = EndDevice(device_id, mac_address, ip_address, subnet_mask)
                    st.session_state.devices[device_id] = new_device
                    st.session_state.network.add_device(new_device)
                    st.success(f"Device {device_id} added with MAC {mac_address} and IP {ip_address}")
                else:
                    st.error(f"Device {device_id} already exists!")
            else:
                st.error("Please provide Device ID, MAC Address, and IP Address.")

def port_assignment():
    if len(st.session_state.devices) > 0:
        selected_device = st.selectbox("Select Device", list(st.session_state.devices.values()), format_func=lambda x: f"{x.id} ({type(x).__name__})")
                    
        with st.form("assign_port"):
            st.subheader("Assign Service Port")
            port_num = st.number_input("Port Number", min_value=1, max_value=65535, value=80)
            protocol = st.selectbox("Protocol", ["tcp", "udp"])
            service = st.selectbox("Service", ["http", "dns", "ftp"])
            
            if st.form_submit_button("Assign Port"):
                handler = None
                if service == "http":
                    handler = http_handler
                elif service == "dns":
                    handler = dns_handler
                elif service == "ftp":
                    handler = ftp_handler
                
                if selected_device.assign_port(port_num, protocol, service, handler):
                    st.session_state.devices[selected_device.id] = selected_device
                    st.success(f"Port {port_num}/{protocol} assigned for {service}")
                else:
                    st.error(f"Port {port_num} is already in use or device doesn't exist")

def add_hub():
    with st.form("add_hub"):
        st.subheader("Add Hub")
        hub_id = st.text_input("Hub ID", key="hub_id")
        
        if st.form_submit_button("Add Hub"):
            if hub_id:
                if hub_id not in st.session_state.hubs:
                    new_hub = Hub(hub_id)
                    st.session_state.hubs[hub_id] = new_hub
                    st.session_state.network.add_hub(new_hub)
                    st.success(f"Hub {hub_id} added")
                else:
                    st.error(f"Hub {hub_id} already exists!")
            else:
                st.error("Please provide a Hub ID.")

def add_switch():
    with st.form("add_switch"):
        st.subheader("Add Switch")
        switch_id = st.text_input("Switch ID", key="switch_id")
        
        if st.form_submit_button("Add Switch"):
            if switch_id:
                if switch_id not in st.session_state.switches:
                    new_switch = Switch(switch_id)
                    st.session_state.switches[switch_id] = new_switch
                    st.session_state.network.add_switch(new_switch)
                    st.success(f"Switch {switch_id} added")
                else:
                    st.error(f"Switch {switch_id} already exists!")
            else:
                st.error("Please provide a Switch ID.")

def add_bridge():
    with st.form("add_bridge"):
        st.subheader("Add Bridge")
        bridge_id = st.text_input("Bridge ID", key="bridge_id")

        if st.form_submit_button("Add Bridge"):
            if bridge_id:
                if bridge_id not in st.session_state.bridges:
                    new_bridge = Bridge(bridge_id)
                    st.session_state.bridges[bridge_id] = new_bridge
                    st.session_state.network.add_bridge(new_bridge)
                    st.success(f"Bridge {bridge_id} added")
                else:
                    st.error(f"Bridge {bridge_id} already exists!")
            else:
                st.error("Please provide a Bridge ID.")

def add_router():
    with st.form("add_router"):
        st.subheader("Add Router")
        router_id = st.text_input("Router ID", key="router_id")
        
        if st.form_submit_button("Add Router"):
            if router_id:
                if router_id not in st.session_state.routers:
                    new_router = Router(router_id)
                    st.session_state.routers[router_id] = new_router
                    st.session_state.network.add_router(new_router)
                    st.success(f"Router {router_id} added")
                else:
                    st.error(f"Router {router_id} already exists!")
            else:
                st.error("Please provide a Router ID.")

def router_interface_configuration():
    routers = list(st.session_state.routers.values())
    if not routers:
        st.info("Add at least one router first")
        return
    
    router = st.selectbox("Select Router", routers, format_func=lambda x: x.id)
    
    with st.form("router_interface"):
        st.subheader(f"Configure Interface for {router.id}")
        interface_name = st.text_input("Interface Name (e.g., eth0)", key="interface_name")
        interface_ip = st.text_input("IP Address", key="interface_ip")
        interface_mac = st.text_input("MAC Address", key="interface_mac") 
        interface_subnet = st.text_input("Subnet Mask", value="255.255.255.0", key="interface_subnet")
        
        if st.form_submit_button("Add Interface"):
            if interface_name and interface_ip and interface_mac:
                router.add_interface(interface_name, interface_ip, interface_mac, interface_subnet)
                st.session_state.routers[router.id] = router
                st.success(f"Interface {interface_name} added to {router.id}")
            else:
                st.error("Please fill all interface details")

def router_routing_configuration():
    routers = list(st.session_state.routers.values())
    if not routers:
        st.info("Add at least one router first")
        return

    router = st.selectbox("Select Router for Routing", routers, format_func=lambda x: x.id)
    
    with st.form("router_route"):
        st.subheader(f"Add Route to {router.id}")
        network = st.text_input("Network Address (e.g. 192.168.1.0)", key="route_network")
        subnet_mask = st.text_input("Subnet Mask", value="255.255.255.0", key="route_subnet")
        
        # Only show interfaces from this router
        interface_options = list(router.interfaces.keys()) if hasattr(router, 'interfaces') else []
        interface = st.selectbox("Exit Interface", [""] + interface_options, key="route_interface")
        
        next_hop = st.text_input("Next Hop IP (leave empty for directly connected)", key="next_hop")
        is_default = st.checkbox("Set as default route", key="is_default")
        
        if st.form_submit_button("Add Route"):
            if is_default:
                if interface and next_hop:
                    router.add_default_route(next_hop, interface)
                    st.session_state.routers[router.id] = router
                    st.success(f"Default route added via {next_hop} on {interface}")
                else:
                    st.error("Interface and next hop required for default route")
            elif network and subnet_mask and interface:
                next_hop_value = next_hop if next_hop else None
                router.add_route(network, subnet_mask, next_hop_value, interface)
                st.session_state.routers[router.id] = router
                st.success(f"Route to {network}/{subnet_mask} added")
            else:
                st.error("Network, subnet mask, and interface are required")

def create_conns(available_entities):
    st.subheader("Create Network Connection")
    entity1 = st.selectbox("Select Entity 1", available_entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
    # Filter out the already selected entity
    remaining_entities = [e for e in available_entities if e != entity1]
    entity2 = st.selectbox("Select Entity 2", remaining_entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
    
    # Get the actual objects from session state (this is crucial)
    def get_actual_entity(entity):
        if isinstance(entity, EndDevice):
            return st.session_state.devices.get(entity.id, entity)
        elif isinstance(entity, Hub):
            return st.session_state.hubs.get(entity.id, entity)
        elif isinstance(entity, Switch):
            return st.session_state.switches.get(entity.id, entity)
        elif isinstance(entity, Bridge):
            return st.session_state.bridges.get(entity.id, entity)
        elif isinstance(entity, Router):
            return st.session_state.routers.get(entity.id, entity)
        return entity
    
    actual_entity1 = get_actual_entity(entity1)
    actual_entity2 = get_actual_entity(entity2)
    
    # Special handling for router connections
    is_router_conn = isinstance(actual_entity1, Router) or isinstance(actual_entity2, Router)
    interface_name = None
    
    if is_router_conn:
        router = actual_entity1 if isinstance(actual_entity1, Router) else actual_entity2
        if hasattr(router, 'interfaces') and router.interfaces:
            interface_options = list(router.interfaces.keys())
            interface_name = st.selectbox("Select Router Interface", interface_options)
        else:
            st.warning(f"Router {router.id} has no configured interfaces. Please add interfaces first.")
            return
    
    # Check if connection already exists
    connection_exists = False
    for conn_entity1, conn_entity2 in st.session_state.connections:
        if (actual_entity1.id == conn_entity1.id and actual_entity2.id == conn_entity2.id) or \
           (actual_entity1.id == conn_entity2.id and actual_entity2.id == conn_entity1.id):
            connection_exists = True
            break
    
    if connection_exists:
        st.warning(f"Connection between {actual_entity1.id} and {actual_entity2.id} already exists!")
    
    if st.button("Connect"):
        if connection_exists:
            st.error(f"Connection between {actual_entity1.id} and {actual_entity2.id} already exists!")
            return
            
        success = False
        message = ""
        
        # Handle router connections differently
        if is_router_conn:
            router = actual_entity1 if isinstance(actual_entity1, Router) else actual_entity2
            other_entity = actual_entity2 if router == actual_entity1 else actual_entity1
            
            if interface_name:
                # Check if they're already connected
                if not any(e.id == other_entity.id for e in router.connected_to) and \
                   not any(e.id == router.id for e in other_entity.connected_to):
                    success = router.connect(other_entity, interface_name)
                    if success:
                        st.session_state.connections.append((router, other_entity))
                        message = f"Connected {other_entity.id} to {router.id} via interface {interface_name}"
                        
                        # If connection to EndDevice, set gateway automatically
                        if isinstance(other_entity, EndDevice):
                            interface_ip = router.interfaces[interface_name]['ip']
                            other_entity.set_gateway(interface_ip)
                            message += f" and set gateway to {interface_ip}"
                    else:
                        message = "Failed to create connection"
                else:
                    message = f"{router.id} and {other_entity.id} are already connected"
            else:
                message = "No router interface selected"
        else:
            # Check if they're already connected
            if not any(e.id == actual_entity2.id for e in actual_entity1.connected_to) and \
               not any(e.id == actual_entity1.id for e in actual_entity2.connected_to):
                success = actual_entity1.connect(actual_entity2)
                if success:
                    st.session_state.connections.append((actual_entity1, actual_entity2))
                    message = f"Connected {actual_entity1.id} and {actual_entity2.id}"
                else:
                    message = "Failed to create connection"
            else:
                message = f"{actual_entity1.id} and {actual_entity2.id} are already connected"
        
        if success:
            st.success(message)
            # Force rerun to update the UI
            # st.rerun()
        else:
            st.error(message)

def send_data(devices, graph_placeholder):
    source = st.selectbox("Source Device", devices, format_func=lambda x: x.id)
    dest = st.selectbox("Destination Device", [d for d in devices if d != source], format_func=lambda x: x.id)
    
    source = st.session_state.devices[source.id]
    dest = st.session_state.devices[dest.id]
    
    layer = st.radio("Network Layer", [1, 2, 3, 4, 5], 
                     format_func=lambda x: {
                         1: "Layer 1 - Physical",
                         2: "Layer 2 - Data Link",
                         3: "Layer 3 - Network",
                         4: "Layer 4 - Transport",
                         5: "Layer 5 - Application"
                     }[x])
    
    if layer >= 4:  
        protocol = st.selectbox("Protocol", ["tcp", "udp"])
        
        dest_ports = {port_num: port for port_num, port in dest.ports.items() 
                     if port['protocol'] == protocol}
        
        if dest_ports:
            port_options = [(p, f"{p} ({dest_ports[p]['service']})") for p in dest_ports]
            dest_port = st.selectbox("Destination Port", 
                                   [p[0] for p in port_options],
                                   format_func=lambda x: f"{x} ({dest_ports[x]['service']})")
            
            # Protocol-specific data
            if dest_ports[dest_port]['service'] == "http":
                data = "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
            elif dest_ports[dest_port]['service'] == "dns":
                data = st.text_input("DNS Query", "example.com")
            elif dest_ports[dest_port]['service'] == "ftp":
                data = st.selectbox("FTP Command", ["LIST", "GET file.txt"])
            else:
                data = st.text_input("Custom Data", "Hello, server!")
        else:
            st.warning(f"No {protocol.upper()} services configured on destination")
            dest_port = st.number_input("Destination Port", min_value=1, max_value=65535, value=80)
            data = st.text_input("Data to send", "Hello, server!")
    else:  
        data = st.text_input("Data to send", "Hello, Network!")
        protocol = None
        dest_port = None
    
    if st.button("Send Data"):
        path = find_path(source, dest, st.session_state.connections)
        print(f"{source.id} sending data to {dest.id}")
        if path:
            sent = False
            
            if layer >= 3 and not source.same_subnet(dest.ip) and not source.default_gateway:
                st.error(f"Source device {source.id} needs a default gateway to reach {dest.id}")
                return
                
            if layer >= 4:
                if 'transport_sim' not in st.session_state:
                    st.session_state.transport_sim = TransportLayerSimulator()
                transport_sim = st.session_state.transport_sim
                
                src_port = transport_sim.get_ephemeral_port(source)
                print(f"Source Port: {src_port} assigned to {source.id}")
                print(f"Destination Port: {dest_port} for {dest.id}")
                print(f"Data to be send: {data}")
                if dest_port not in dest.ports or dest.ports[dest_port]['protocol'] != protocol:
                    transport_sim.log_message(source, dest, 
                                            f"Connection refused (port {dest_port} closed)", 
                                            src_port, dest_port, protocol)
                    st.error(f"Port {dest_port}/{protocol} is not open on destination")
                    return
                
                service = dest.ports[dest_port]
                print(f"Service: {service}")
                if service['handler']:
                    response = service['handler'](data)
                    
                sent = source.send(data, dest, layer=3)
            else:
                sent = source.send(data, dest, layer=layer)
            
            if sent:
                msg = {
                    "source": source.id,
                    "destination": dest.id,
                    "data": data,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "path": path,
                    "layer": layer
                }
                
                if layer >= 2:
                    msg["source_mac"] = source.mac
                    msg["dest_mac"] = dest.mac
                
                if layer >= 3:
                    msg["source_ip"] = source.ip
                    msg["dest_ip"] = dest.ip
                
                if layer >= 4:
                    msg["source_port"] = src_port
                    msg["dest_port"] = dest_port
                    msg["protocol"] = protocol
                
                st.session_state.messages.append(msg)
                
                html = visualize_topology(st.session_state.network, st.session_state.connections, highlight_path=path)
                graph_placeholder.empty()  
                st.components.v1.html(html, height=500)  
                
                st.success(f"Data sent from {source.id} to {dest.id} using Layer {layer}")
            else:
                st.error(f"Failed to send data to {dest.id}")
        else:
            st.error(f"No path found between {source.id} and {dest.id}")

def vlan_configuration():
    switches = list(st.session_state.switches.values())
    if not switches:
        st.info("Add at least one switch first")
        return
        
    switch = st.selectbox("Select Switch", switches, format_func=lambda x: x.id)
    
    # Display current VLAN configuration
    if hasattr(switch, 'vlan_table') and switch.vlan_table:
        st.write("**Current VLAN Configuration:**")
        for port, vlan in switch.vlan_table.items():
            # Find the device connected to this port
            device_name = "Unknown"
            for device, port_num in switch.port_table.items():
                if port_num == port:
                    device_name = device.id
                    break
            st.write(f"Port {port} ({device_name}): VLAN {vlan}")
    
    # Configure VLAN for a device
    with st.form("vlan_config"):
        st.subheader("Configure VLAN")
        
        # Show only devices connected to this switch
        connected_devices = [device for device in switch.connected_to]
        if not connected_devices:
            st.warning("No devices connected to this switch")
            st.form_submit_button("Set VLAN", disabled=True)
            return
            
        device = st.selectbox("Select Device", connected_devices, format_func=lambda x: x.id)
        vlan_id = st.number_input("VLAN ID", min_value=1, max_value=4094, value=1)
        
        if st.form_submit_button("Set VLAN"):
            if switch.set_port_vlan(device, vlan_id):
                # Update the switch in session state
                st.session_state.switches[switch.id] = switch
                st.success(f"Set {device.id} to VLAN {vlan_id}")
            else:
                st.error("Failed to set VLAN")

def arp_management():
    devices = list(st.session_state.devices.values())
    if not devices:
        st.info("Add at least one device first")
        return
        
    device = st.selectbox("Select Device", devices, format_func=lambda x: x.id)
    
    # Display current ARP table
    if hasattr(device, 'arp_table') and device.arp_table:
        st.write("**Current ARP Table:**")
        for ip, mac in device.arp_table.items():
            st.write(f"IP: {ip} → MAC: {mac}")
    else:
        st.write("ARP table is empty")
    
    # Add a static ARP entry
    with st.form("arp_entry"):
        st.subheader("Add Static ARP Entry")
        ip_address = st.text_input("IP Address", key="arp_ip")
        mac_address = st.text_input("MAC Address", key="arp_mac")
        
        if st.form_submit_button("Add Entry"):
            if ip_address and mac_address:
                device.add_to_arp_table(ip_address, mac_address)
                # Update device in session state
                st.session_state.devices[device.id] = device
                st.success(f"Added ARP entry: {ip_address} → {mac_address}")
            else:
                st.error("Please provide both IP and MAC address")

def layerSimulation():
    graph_placeholder = st.empty()
    initialize_session_state(Network)
    # restore_connections()
    # Create a two-column layout
    col1, col2 = st.columns([2, 3])

    with col1:
        st.header("Network Configuration")

        with st.expander("Prebuilt Networks", expanded=True):
            prebuilt_network_ui()
        
        with st.expander("Add Network Components", expanded=True):
            add_device()
            port_assignment()
            add_hub()
            add_switch()
            add_bridge()
            add_router()

        with st.expander("Router Configuration", expanded=True):
            router_interface_configuration()
            router_routing_configuration()
            
        with st.expander("Create Connections", expanded=True):
            available_entities = list(st.session_state.devices.values()) + list(st.session_state.hubs.values())
            available_entities += list(st.session_state.switches.values()) + list(st.session_state.bridges.values()) + list(st.session_state.routers.values())
            
            if len(available_entities) >= 2:
                create_conns(available_entities)

        # Data Transmission 
        with st.expander("Send Data", expanded=True):
            devices = list(st.session_state.devices.values())
            if len(devices) >= 2:
                send_data(devices, graph_placeholder)

        with st.expander("Network Layer Features", expanded=True):
            tab1, tab2, tab3 = st.tabs(["MAC Tables", "VLANs", "ARP Tables"])
            
            with tab1:
                st.subheader("MAC Address Table Management")
                
                # Get list of switches and bridges
                network_devices = list(st.session_state.switches.values()) + list(st.session_state.bridges.values())
                if network_devices:
                    selected_device = st.selectbox("Select Device", network_devices, format_func=lambda x: x.id)
                    
                    # Show current MAC table
                    if hasattr(selected_device, 'mac_table'):
                        st.write("**Current MAC Address Table:**")
                        for mac, port in selected_device.mac_table.items():
                            # Find the device connected to this port
                            device_name = "Unknown"
                            for device, port_num in selected_device.port_table.items():
                                if port_num == port:
                                    device_name = device.id
                                    break
                            st.write(f"MAC: {mac} → Port: {port} ({device_name})")
                    else:
                        st.write("MAC table is empty.")
                else:
                    st.info("Add at least one switch or bridge to use MAC table features.")
            
            with tab2:
                vlan_configuration()
                
            with tab3:
                arp_management()

    if st.sidebar.button("Restore Connections"):
        restore_connections()
        st.sidebar.success("Connections restored!")

    with col2:
        st.header("Network Topology")
        
        # Include all connections for visualization
        visible_connections = st.session_state.connections
        
        html = visualize_topology(st.session_state.network, visible_connections)
        graph_placeholder.empty()  
        st.components.v1.html(html, height=500)  
        
        with st.expander("Message History", expanded=True):
            layer_messages = st.session_state.messages
            
            if layer_messages:
                for idx, msg in enumerate(reversed(layer_messages)):
                    st.write(f"**{msg['timestamp']}**: {msg['source']} → {msg['destination']}")
                    
                    # Show layer-specific details
                    if msg['layer'] <= 3:
                        st.text(f"Data: {msg['data']}")
                        st.text(f"Path: {' → '.join(msg['path'])}")
                        st.text(f"Layer: {msg['layer']} ({['Physical', 'Data Link', 'Network'][msg['layer']-1]})")
                        
                        if 'source_mac' in msg and 'dest_mac' in msg:
                            st.text(f"Source MAC: {msg['source_mac']}, Destination MAC: {msg['dest_mac']}")
                            
                        if 'source_ip' in msg and 'dest_ip' in msg:
                            st.text(f"Source IP: {msg['source_ip']}, Destination IP: {msg['dest_ip']}")
                    else:
                        # Transport/Application layer messages
                        st.text(f"Layer: {msg['layer']} ({['Transport', 'Application'][msg['layer']-4]})")
                        st.text(f"Protocol: {msg.get('protocol', '').upper()}")
                        st.text(f"Source Port: {msg.get('source_port', '')}")
                        st.text(f"Dest Port: {msg.get('dest_port', '')}")
                        st.code(msg['data'])
                    
                    if idx < len(layer_messages) - 1:
                        st.divider()
            else:
                st.info("No messages sent yet.")
        
        with st.expander("Network Information", expanded=True):
            tab1, tab2, tab3 = st.tabs(["End Devices", "Networking Devices", "Routers"])
            
            with tab1:
                st.subheader("End Devices")
                if st.session_state.devices:
                    for device_id, device in st.session_state.devices.items():
                        st.write(f"**Device**: {device_id}")
                        st.write(f"MAC: {device.mac}")
                        st.write(f"IP: {device.ip}/{device.subnet_mask}")
                        
                        if device.default_gateway:
                            st.write(f"Default Gateway: {device.default_gateway}")
                        else:
                            st.write("Default Gateway: Not set")
                        
                        connected_to = [conn_entity.id for conn_entity in device.connected_to]
                        
                        if connected_to:
                            st.write(f"Connected to: {', '.join(connected_to)}")
                        else:
                            st.write("Connected to: None")
                        
                        # Show ARP table
                        if hasattr(device, 'arp_table') and device.arp_table:
                            st.write("**ARP Table:**")
                            for ip, mac in device.arp_table.items():
                                st.write(f"IP: {ip} → MAC: {mac}")
                        
                        # Show services
                        if hasattr(device, 'ports') and device.ports:
                            st.write("**Services:**")
                            for port_num, port_info in device.ports.items():
                                st.write(f"Port {port_num}/{port_info['protocol']}: {port_info['service']}")
                        
                        # Show received data 
                        if hasattr(device, 'received_data') and device.received_data:
                            st.write(f"**Received Data ({len(device.received_data)}):**")
                            for data in device.received_data:
                                layer = data.get('layer', 1)
                                source = data.get('source', 'Unknown')
                                
                                if layer == 1:
                                    st.write(f"Layer 1 data from {source}")
                                elif layer == 2:
                                    frame = data.get('frame', {})
                                    src_mac = frame.get('source_mac', 'Unknown')
                                    st.write(f"Layer 2 frame from {source} (MAC: {src_mac})")
                                elif layer == 3:
                                    packet = data.get('packet', {})
                                    src_ip = packet.get('source_ip', 'Unknown')
                                    st.write(f"Layer 3 packet from {source} (IP: {src_ip})")
                                elif layer >= 4:
                                    protocol = data.get('protocol', '').upper()
                                    src_port = data.get('source_port', '')
                                    st.write(f"Layer {layer} {protocol} data from {source}:{src_port}")
                        st.divider()
                else:
                    st.info("No devices added yet.")
            
            with tab2:
                st.subheader("Hubs")
                if st.session_state.hubs:
                    for hub_id, hub in st.session_state.hubs.items():
                        st.write(f"**Hub**: {hub_id}")
                        
                        connected_to = [conn_entity.id for conn_entity in hub.connected_to]
                        
                        if connected_to:
                            st.write(f"Connected to: {', '.join(connected_to)}")
                        else:
                            st.write("Connected to: None")
                        
                        st.divider()
                else:
                    st.info("No hubs added yet.")
                
                st.subheader("Switches")
                if st.session_state.switches:
                    for switch_id, switch in st.session_state.switches.items():
                        st.write(f"**Switch**: {switch_id}")
                        
                        connected_to = [conn_entity.id for conn_entity in switch.connected_to]
                        
                        if connected_to:
                            st.write(f"Connected to: {', '.join(connected_to)}")
                        else:
                            st.write("Connected to: None")
                        
                        if hasattr(switch, 'mac_table') and switch.mac_table:
                            st.write("**MAC Address Table:**")
                            for mac, port in switch.mac_table.items():
                                device_name = "Unknown"
                                for device, port_num in switch.port_table.items():
                                    if port_num == port:
                                        device_name = device.id
                                        break
                                st.write(f"MAC: {mac} → Port: {port} ({device_name})")
                        
                        if hasattr(switch, 'vlan_table') and switch.vlan_table:
                            st.write("**VLAN Table:**")
                            for port, vlan in switch.vlan_table.items():
                                device_name = "Unknown"
                                for device, port_num in switch.port_table.items():
                                    if port_num == port:
                                        device_name = device.id
                                        break
                                st.write(f"Port: {port} ({device_name}) → VLAN: {vlan}")
                        
                        st.divider()
                else:
                    st.info("No switches added yet.")
                
                st.subheader("Bridges")
                if st.session_state.bridges:
                    for bridge_id, bridge in st.session_state.bridges.items():
                        st.write(f"**Bridge**: {bridge_id}")
                
                        connected_to = [conn_entity.id for conn_entity in bridge.connected_to]
                        st.write(f"Connected to: {', '.join(connected_to) if connected_to else 'None'}")
                
                        if hasattr(bridge, 'mac_table') and bridge.mac_table:
                            st.write("**MAC Address Table:**")
                            for mac, port in bridge.mac_table.items():
                                device_name = "Unknown"
                                for device, port_num in bridge.port_table.items():
                                    if port_num == port:
                                        device_name = device.id
                                        break
                                st.write(f"MAC: {mac} → Port: {port} ({device_name})")
                
                        st.divider()
                else:
                    st.info("No bridges added yet.")
            
            with tab3:
                st.subheader("Routers")
                if st.session_state.routers:
                    for router_id, router in st.session_state.routers.items():
                        st.write(f"**Router**: {router_id}")
                        
                        connected_to = [conn_entity.id for conn_entity in router.connected_to]
                        st.write(f"Connected to: {', '.join(connected_to) if connected_to else 'None'}")
                        
                        # Show interfaces
                        if hasattr(router, 'interfaces') and router.interfaces:
                            st.write("**Interfaces:**")
                            for name, details in router.interfaces.items():
                                st.write(f"Interface: {name}")
                                st.write(f"  IP: {details['ip']}")
                                st.write(f"  MAC: {details['mac']}")
                                st.write(f"  Subnet: {details['subnet_mask']}")
                        else:
                            st.write("No interfaces configured")
                            
                        # Show routing table
                        if hasattr(router, 'routing_table') and router.routing_table:
                            st.write("**Routing Table:**")
                            for route in router.routing_table:
                                if route['network'] == "0.0.0.0" and route['subnet_mask'] == "0.0.0.0":
                                    st.write(f"Default route → Next Hop: {route['next_hop']}, Interface: {route['interface']}")
                                else:
                                    next_hop = route['next_hop'] if route['next_hop'] else "Direct"
                                    st.write(f"Network: {route['network']}/{route['subnet_mask']} → Next Hop: {next_hop}, Interface: {route['interface']}")
                        else:
                            st.write("Routing table is empty")
                        
                        st.divider()
                else:
                    st.info("No routers added yet.")
            
            st.subheader("Network Statistics")
            total_devices = len(st.session_state.devices)
            total_hubs = len(st.session_state.hubs)
            total_switches = len(st.session_state.switches)
            total_bridges = len(st.session_state.bridges)
            total_routers = len(st.session_state.routers)
            total_connections = len(visible_connections)
            
            st.write(f"Total Devices: {total_devices}")
            st.write(f"Total Hubs: {total_hubs}")
            st.write(f"Total Switches: {total_switches}")
            st.write(f"Total Bridges: {total_bridges}")
            st.write(f"Total Routers: {total_routers}")
            st.write(f"Total Connections: {total_connections}")
            
            # Calculate broadcast domains
            broadcast_domains = total_switches + total_routers
            
            if total_bridges > 0:
                broadcast_domains += 1
            
            if broadcast_domains == 0 and (total_hubs > 0 or total_devices > 0):
                broadcast_domains = 1  # At least one broadcast domain if devices exist
            
            st.write(f"Total Broadcast Domains: {broadcast_domains}")
            
            # Calculate collision domains
            collision_domains = sum(len([conn for conn in switch.connected_to if not isinstance(conn, Hub)]) 
                                  for switch in st.session_state.switches.values())
            collision_domains += sum(len([conn for conn in bridge.connected_to if not isinstance(conn, Hub)]) 
                                    for bridge in st.session_state.bridges.values())
            collision_domains += sum(len([conn for conn in router.connected_to if not isinstance(conn, Hub)]) 
                                    for router in st.session_state.routers.values())
            collision_domains += total_hubs
            
            if collision_domains == 0 and total_devices > 0:
                collision_domains = 1
                
            st.write(f"Total Collision Domains: {collision_domains}")

    if st.button("Reset Network"):
        for key in ['network', 'devices', 'hubs', 'switches', 'bridges', 'connections', 'messages', 'routers', 'transport_sim']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()