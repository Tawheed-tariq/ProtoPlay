import streamlit as st
from core.devices import EndDevice, Hub, Switch ,Bridge
from core.network import Network
import time
from core.functions import visualize_topology, find_path, restore_connections, initialize_session_state


def add_device():
    with st.form("add_device"):
        st.subheader("Add End Device")
        device_id = st.text_input("Device ID", key="device_id")
        mac_address = st.text_input("MAC Address (format: XX:XX:XX:XX:XX:XX)", key="mac_address")
        
        if st.form_submit_button("Add Device"):
            if device_id and mac_address:
                if device_id not in st.session_state.devices:
                    new_device = EndDevice(device_id, mac_address)
                    st.session_state.devices[device_id] = new_device
                    st.session_state.network.add_device(new_device)
                    st.success(f"Device {device_id} added with MAC {mac_address}")
                else:
                    st.error(f"Device {device_id} already exists!")
            else:
                st.error("Please provide both Device ID and MAC Address.")

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
                    new_bridge = Bridge(bridge_id)  # Assuming you have a Bridge class
                    st.session_state.bridges[bridge_id] = new_bridge
                    st.session_state.network.add_bridge(new_bridge)
                    st.success(f"Bridge {bridge_id} added")
                else:
                    st.error(f"Bridge {bridge_id} already exists!")
            else:
                st.error("Please provide a Bridge ID.")

def create_conns(available_entities):
    st.subheader("Create Network Connection")
    entity1 = st.selectbox("Select Entity 1", available_entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
    # Filter out the already selected entity
    remaining_entities = [e for e in available_entities if e != entity1]
    entity2 = st.selectbox("Select Entity 2", remaining_entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
    
    if st.button("Connect"):
        # Create the connection in the network
        success, message = st.session_state.network.connect(entity1, entity2)
        
        if success:
            # Get fresh copies from session state to ensure we're using the current state
            if isinstance(entity1, EndDevice):
                entity1 = st.session_state.devices[entity1.id]
            elif isinstance(entity1, Hub):
                entity1 = st.session_state.hubs[entity1.id]
            elif isinstance(entity1, Switch):
                entity1 = st.session_state.switches[entity1.id]
            elif isinstance(entity1, Bridge):
                entity1 = st.session_state.bridges[entity1.id]    
                
            if isinstance(entity2, EndDevice):
                entity2 = st.session_state.devices[entity2.id]
            elif isinstance(entity2, Hub):
                entity2 = st.session_state.hubs[entity2.id]
            elif isinstance(entity2, Switch):
                entity2 = st.session_state.switches[entity2.id]
            elif isinstance(entity2, Bridge):
                entity2 = st.session_state.bridges[entity2.id]    
            
            # Add the connection to our list
            st.session_state.connections.append((entity1, entity2))
            
            # Apply connections directly
            entity1.connect(entity2)
            entity2.connect(entity1)
            
            # Update entities in session state
            if isinstance(entity1, EndDevice):
                st.session_state.devices[entity1.id] = entity1
            elif isinstance(entity1, Hub):
                st.session_state.hubs[entity1.id] = entity1
            elif isinstance(entity1, Switch):
                st.session_state.switches[entity1.id] = entity1
            elif isinstance(entity1, Bridge):
                st.session_state.bridges[entity1.id] = entity1    
                
            if isinstance(entity2, EndDevice):
                st.session_state.devices[entity2.id] = entity2
            elif isinstance(entity2, Hub):
                st.session_state.hubs[entity2.id] = entity2
            elif isinstance(entity2, Switch):
                st.session_state.switches[entity2.id] = entity2
            elif isinstance(entity2, Bridge):
                st.session_state.bridges[entity2.id] = entity2
                    
            st.success(f"Connected {entity1.id} and {entity2.id}")
        else:
            st.error(message)
    else:
        st.info("Add at least two network components to create connections.")

def send_data(devices, layer_options, graph_placeholder):
    source = st.selectbox("Source Device", devices, format_func=lambda x: x.id)
    dest = st.selectbox("Destination Device", [d for d in devices if d != source], format_func=lambda x: x.id)
    data = st.text_input("Data to send", "Hello, Network!")
    
    if st.button("Send Data"):
        # Make sure we're using current objects
        source = st.session_state.devices[source.id]
        dest = st.session_state.devices[dest.id]
        
        # Check if there's a valid path given the current layer
        # In Layer 1, we can only connect if there's a physical path through devices and hubs
        # In Layer 2+, we can also use switches
        valid_connections = []
        for conn in st.session_state.connections:
            # For Layer 1, exclude connections involving switches
            if st.session_state.selected_layer == 1:
                if not (isinstance(conn[0], Switch) or isinstance(conn[1], Switch) or 
                    isinstance(conn[0], Bridge) or isinstance(conn[1], Bridge)):
                    valid_connections.append(conn)
            else:
                # For Layer 2+, include all connections
                valid_connections.append(conn)
        
        # Find path between source and destination using valid connections
        path = find_path(source, dest, valid_connections)
        
        if path:
            # Send data using selected layer
            layer = st.session_state.selected_layer
            sent = source.send(data, dest, layer=layer)
            
            if sent:
                # Record the message
                st.session_state.messages.append({
                    "source": source.id,
                    "destination": dest.id,
                    "data": data,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "path": path,
                    "layer": layer
                })
                
                # Highlight the path during data transfer
                html = visualize_topology(st.session_state.network, valid_connections, highlight_path=path)
                graph_placeholder.empty()  # Clear the previous graph
                st.components.v1.html(html, height=500)  # Render the new graph
                
                st.success(f"Data sent from {source.id} to {dest.id} using {layer_options[layer]}")
            else:
                st.error(f"Failed to send data to {dest.id}")
        else:
            st.error(f"No path found between {source.id} and {dest.id} in {layer_options[layer]}")
    else:
        st.info("Add at least two devices to send data.")

def layerSimulation(selected_layer, layer_options):
    st.session_state.selected_layer = selected_layer
    graph_placeholder = st.empty()
    initialize_session_state(Network)
    restore_connections()
    # Create a two-column layout
    col1, col2 = st.columns([2, 3])

    with col1:
        st.header(f"Network Configuration - {layer_options[selected_layer]}")
        
        with st.expander("Add Network Components", expanded=True):
            add_device()
            add_hub()
            if st.session_state.selected_layer >= 2:
                add_switch()
                add_bridge()
                
        with st.expander("Create Connections", expanded=True):
            available_entities = list(st.session_state.devices.values()) + list(st.session_state.hubs.values())
            if st.session_state.selected_layer >= 2:
                available_entities += list(st.session_state.switches.values()) + list(st.session_state.bridges.values())
            
            if len(available_entities) >= 2:
                create_conns(available_entities)


        # Data Transmission - Layer-specific behavior
        with st.expander("Send Data", expanded=True):
            if st.session_state.selected_layer == 1:
                st.info("Physical Layer Mode: Data transmission uses broadcast with hubs and unicast between directly connected devices.")
            else:  
                st.info("Data Link Layer Mode: Switches and Bridges use MAC addresses for intelligent forwarding, while hubs continue to broadcast.")
                
            devices = list(st.session_state.devices.values())
            if len(devices) >= 2:
                send_data(devices, layer_options, graph_placeholder)

        if st.session_state.selected_layer >= 2:
            with st.expander("Data Link Layer Features", expanded=True):
                st.subheader("MAC Address Table Management")
                
                # Get list of switches and bridges
                network_devices = list(st.session_state.switches.values()) + list(st.session_state.bridges.values())
                if network_devices:
                    selected_device = st.selectbox("Select Device", network_devices, format_func=lambda x: x.id)
                    
                    # Show current MAC table
                    if hasattr(selected_device, 'mac_table'):
                        st.write("**Current MAC Address Table:**")
                        for mac, port in selected_device.mac_table.items():
                            st.write(f"MAC: {mac} → Port: {port}")
                        else:
                            st.write("MAC table is empty.")
                    
                    # Option to clear MAC table
                    if st.button("Clear MAC Table"):
                        if hasattr(selected_device, 'clear_mac_table'):
                            selected_device.clear_mac_table()
                            if isinstance(selected_device, Switch):
                                st.session_state.switches[selected_device.id] = selected_device
                        elif isinstance(selected_device, Bridge):
                            st.session_state.bridges[selected_device.id] = selected_device
                            st.success(f"Cleared MAC table for : {selected_device.id}")
                        else:
                            st.error("This switch doesn't support clearing the MAC table.")
                else:
                    st.info("Add at least one switch or bridge to use MAC table features.")

    if st.sidebar.button("Restore Connections"):
        restore_connections()
        st.sidebar.success("Connections restored!")

    with col2:
        st.header("Network Topology")
        
        # Filter connections based on layer for visualization
        visible_connections = []
        for conn in st.session_state.connections:
            # For Layer 1, exclude connections involving switches
            if st.session_state.selected_layer == 1:
                if not (isinstance(conn[0], Switch) or isinstance(conn[1], Switch)):
                    visible_connections.append(conn)
            else:
                # For Layer 2+, include all connections
                visible_connections.append(conn)
        
        # Initial visualization of the topology with layer-appropriate connections
        html = visualize_topology(st.session_state.network, visible_connections)
        graph_placeholder.empty()  # Clear the placeholder
        st.components.v1.html(html, height=500)  # Render the initial graph
        
        # Message history with layer information
        with st.expander("Message History", expanded=True):
            # Filter messages based on layer
            layer_messages = [msg for msg in st.session_state.messages if msg.get('layer', 1) <= st.session_state.selected_layer]
            
            if layer_messages:
                for idx, msg in enumerate(reversed(layer_messages)):
                    layer_info = msg.get('layer', 1)  # Default to physical if not specified
                    layer_name = layer_options[layer_info]
                    
                    st.write(f"**{msg['timestamp']}**: {msg['source']} → {msg['destination']} ({layer_name})")
                    st.text(f"Data: {msg['data']}")
                    st.text(f"Path: {' → '.join(msg['path'])}")
                    
                    # Show additional layer-specific information
                    if layer_info == 2:
                        # For data link layer messages, we might want to show MAC addresses used
                        if 'source_mac' in msg and 'dest_mac' in msg:
                            st.text(f"Source MAC: {msg['source_mac']}, Destination MAC: {msg['dest_mac']}")
                    
                    if idx < len(layer_messages) - 1:
                        st.divider()
            else:
                st.info("No messages sent yet.")
        
        # Show network information - filter components based on layer
        with st.expander("Network Information", expanded=True):
            # Display devices - always visible
            st.subheader("Devices")
            if st.session_state.devices:
                for device_id, device in st.session_state.devices.items():
                    st.write(f"**Device**: {device_id}")
                    st.write(f"MAC: {device.mac}")
                    
                    # Filter connected_to display based on layer
                    connected_to = []
                    for conn_entity in device.connected_to:
                        # In Layer 1, only show connections to devices and hubs
                        if st.session_state.selected_layer == 1:
                            if not isinstance(conn_entity, Switch):
                                connected_to.append(conn_entity.id)
                        else:
                            # In Layer 2+, show all connections
                            connected_to.append(conn_entity.id)
                    
                    if connected_to:
                        st.write(f"Connected to: {', '.join(connected_to)}")
                    else:
                        st.write("Connected to: None")
                    
                    # Show received messages filtered by layer
                    layer_received = [data for data in device.received_data if data.get('layer', 1) <= st.session_state.selected_layer]
                    if layer_received:
                        st.subheader(f"Received Data ({len(layer_received)})")
                        for data in layer_received:
                            received_via = data.get('layer', 1)
                            layer_name = layer_options[received_via]
                            st.write(f"From {data['source']} via {layer_name}: {data['data']}")
                    st.divider()
            else:
                st.info("No devices added yet.")
            
            # Display hubs - always visible
            st.subheader("Hubs")
            if st.session_state.hubs:
                for hub_id, hub in st.session_state.hubs.items():
                    st.write(f"**Hub**: {hub_id}")
                    
                    # Filter connected_to display based on layer
                    connected_to = []
                    for conn_entity in hub.connected_to:
                        # In Layer 1, only show connections to devices and hubs
                        if st.session_state.selected_layer == 1:
                            if not isinstance(conn_entity, Switch):
                                connected_to.append(conn_entity.id)
                        else:
                            # In Layer 2+, show all connections
                            connected_to.append(conn_entity.id)
                    
                    if connected_to:
                        st.write(f"Connected to: {', '.join(connected_to)}")
                    else:
                        st.write("Connected to: None")
                    
                    st.divider()
            else:
                st.info("No hubs added yet.")
            
            # Display switches - only visible in Layer 2+
            if st.session_state.selected_layer >= 2:
                st.subheader("Switches and Bridges")
                
                if st.session_state.switches or st.session_state.bridges:
                    # Display Switches
                    for switch_id, switch in st.session_state.switches.items():
                        st.write(f"**Switch**: {switch_id}")
                        
                        # Update connected_to display
                        connected_to = []
                        for conn_entity in switch.connected_to:
                            connected_to.append(conn_entity.id)
                        
                        if connected_to:
                            st.write(f"Connected to: {', '.join(connected_to)}")
                        else:
                            st.write("Connected to: None")
                        
                        # Display MAC Address Table if it exists
                        if hasattr(switch, 'mac_table'):
                            st.write("**MAC Address Table:**", unsafe_allow_html=True)
                            
                            if switch.mac_table:
                                for mac, port in switch.mac_table.items():
                                    st.write(f"MAC: {mac} → Port: {port}")
                            else:
                                st.write("MAC table is empty.")
                        
                        st.divider()
                        # Display Bridges
                    for bridge_id, bridge in st.session_state.bridges.items():
                        st.write(f"**Bridge**: {bridge_id}")
                
                        connected_to = [conn_entity.id for conn_entity in bridge.connected_to]
                        st.write(f"Connected to: {', '.join(connected_to) if connected_to else 'None'}")
                
                        # if hasattr(bridge, 'fdb'):
                        #     st.write("**Filtering Database (FDB):**", unsafe_allow_html=True)
                        # if bridge.fdb:
                        #     for mac, port in bridge.fdb.items():
                        #         st.write(f"MAC: {mac} → Port: {port}")          
                        
                        # else:
                        #     st.write("FDB is empty.")
                
                        st.divider()
                else:
                    st.info("No switches and bridges are added yet.")
                    
            
            # Layer-specific network statistics
            if st.session_state.selected_layer == 1:
                # Show physical layer statistics
                st.subheader("Physical Layer Statistics")
                total_devices = len(st.session_state.devices)
                total_hubs = len(st.session_state.hubs)
                total_connections = len(visible_connections)  # Only count visible connections
                
                st.write(f"Total Devices: {total_devices}")
                st.write(f"Total Hubs: {total_hubs}")
                st.write(f"Total Connections: {total_connections}")
                
                # Calculate broadcast domains in physical layer (each hub creates one domain)
                broadcast_domains = total_hubs
                if broadcast_domains == 0 and total_devices > 0:
                    broadcast_domains = 1  # At least one broadcast domain if devices exist
                st.write(f"Total Broadcast Domains: {broadcast_domains}")
                
            else:  # data_link layer statistics
                st.subheader("Data Link Layer Statistics")
                total_devices = len(st.session_state.devices)
                total_hubs = len(st.session_state.hubs)
                total_switches = len(st.session_state.switches)
                total_bridges=len(st.session_state.bridges)
                
                st.write(f"Total Devices: {total_devices}")
                st.write(f"Total Hubs: {total_hubs}")
                st.write(f"Total Switches: {total_switches}")
                st.write(f"Total Bridges :{total_bridges}")
                
                # Calculate broadcast domains in data link layer 
                # (each switch creates one domain, each hub shares a domain)
                broadcast_domains = total_switches + total_bridges
                if total_hubs > 0 or (total_devices > 0 and total_switches + total_bridges== 0):
                    broadcast_domains += 1  # Add one domain for all connected hubs
                st.write(f"Total Broadcast Domains: {broadcast_domains}")
                
                # Calculate collision domains
                # In data link layer: switches create separate collision domains for each port
                # Count connections to switches plus one domain for each hub
                
                collision_domains = sum(len(switch.connected_to) for switch in st.session_state.switches.values())
                collision_domains += sum(len(bridge.connected_to) for bridge in st.session_state.bridges.values())
                collision_domains += total_hubs
                if collision_domains == 0 and total_devices > 0:
                    collision_domains = 1
                st.write(f"Total Collision Domains: {collision_domains}")
                
                #collision_domains = 0
                #for switch in st.session_state.switches.values():
                #   collision_domains += len(switch.connected_to)
                #collision_domains += total_hubs  # Each hub is one collision domain
                #if collision_domains == 0 and total_devices > 0:
                #   collision_domains = 1  # At least one collision domain if devices exist
                #st.write(f"Total Collision Domains: {collision_domains}")

    # Add reset button at the bottom
    if st.button("Reset Network"):
        for key in ['network', 'devices', 'hubs', 'switches', 'bridges' ,'connections', 'messages', 'selected_layer']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()