import streamlit as st
from core.physical import EndDevice, Hub, Network
import networkx as nx
from pyvis.network import Network as PyVisNetwork
import time
import os

# Set page title and layout
st.set_page_config(page_title="Network Simulator", layout="wide")

# Initialize network and session state
if 'network' not in st.session_state:
    st.session_state.network = Network()

# Store devices and hubs in session state
if 'devices' not in st.session_state:
    st.session_state.devices = {}  # Store devices by ID
if 'hubs' not in st.session_state:
    st.session_state.hubs = {}  # Store hubs by ID

# Store connections in session state
if 'connections' not in st.session_state:
    st.session_state.connections = []  # List of connections (entity1, entity2)

# Track transmitted messages
if 'messages' not in st.session_state:
    st.session_state.messages = []  # List of transmitted messages

# Create a placeholder for the graph
graph_placeholder = st.empty()

def visualize_topology(network, connections, highlight_path=None):
    """
    Generate the PyVis graph and return the HTML content.
    """
    G = nx.Graph()

    # Add all devices and hubs to the graph
    for device in network.devices:
        G.add_node(device.id, label=f"{device.id}\n{device.mac}", color='#6495ED', title=f"Device: {device.id}\nMAC: {device.mac}")
    
    for hub in network.hubs:
        G.add_node(hub.id, label=f"Hub {hub.id}", color='#FF6347', shape='diamond', title=f"Hub: {hub.id}")

    # Add all connections to the graph
    for conn in connections:
        G.add_edge(conn[0].id, conn[1].id)
    
    # Highlight the path if data is being transferred
    if highlight_path:
        for i in range(len(highlight_path) - 1):
            if (highlight_path[i], highlight_path[i + 1]) in G.edges:
                G.edges[(highlight_path[i], highlight_path[i + 1])]['color'] = '#32CD32'
                G.edges[(highlight_path[i], highlight_path[i + 1])]['width'] = 3

    # Create a PyVis network
    net = PyVisNetwork(height="500px", width="100%", notebook=False)
    net.from_nx(G)
    
    # Configure physics for better visualization
    net.toggle_physics(True)
    net.barnes_hut(spring_length=200, spring_strength=0.05)
    
    # Save the graph to a temporary file
    os.makedirs('temp', exist_ok=True)
    graph_path = "temp/network_graph.html"
    net.save_graph(graph_path)
    
    with open(graph_path, "r", encoding="utf-8") as f:
        html = f.read()
    return html

def find_path(source, destination, connections):
    """
    Find the path between two devices in the network.
    Returns a list of entity IDs representing the path.
    """
    G = nx.Graph()
    
    # Add all connections to the graph
    for conn in connections:
        G.add_edge(conn[0].id, conn[1].id)

    try:
        path = nx.shortest_path(G, source=source.id, target=destination.id)
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

# Restore connections from session state - This is critical
def restore_connections():
    for conn in st.session_state.connections:
        entity1, entity2 = conn
        
        # Ensure both entities are available
        if (isinstance(entity1, EndDevice) and entity1.id in st.session_state.devices) or \
           (isinstance(entity1, Hub) and entity1.id in st.session_state.hubs):
            if (isinstance(entity2, EndDevice) and entity2.id in st.session_state.devices) or \
               (isinstance(entity2, Hub) and entity2.id in st.session_state.hubs):
                
                # Get the current instances
                if isinstance(entity1, EndDevice):
                    entity1 = st.session_state.devices[entity1.id]
                else:
                    entity1 = st.session_state.hubs[entity1.id]
                    
                if isinstance(entity2, EndDevice):
                    entity2 = st.session_state.devices[entity2.id]
                else:
                    entity2 = st.session_state.hubs[entity2.id]
                
                # Make sure they're connected
                if entity2 not in entity1.connected_to:
                    entity1.connect(entity2)
                if entity1 not in entity2.connected_to:
                    entity2.connect(entity1)

# Restore connections at the beginning
restore_connections()

# Streamlit UI
st.title("Network Simulator - Physical Layer")

# Create a two-column layout
col1, col2 = st.columns([2, 3])

with col1:
    st.header("Network Configuration")
    
    # Add devices and hubs
    with st.expander("Add Devices & Hubs", expanded=True):
        # Add End Device
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
        
        # Add Hub
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
    
    # Connection Management
    with st.expander("Create Connections", expanded=True):
        entities = (list(st.session_state.devices.values()) + 
                   list(st.session_state.hubs.values()))
        
        if len(entities) >= 2:
            entity1 = st.selectbox("Select Entity 1", entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
            # Filter out the already selected entity
            remaining_entities = [e for e in entities if e != entity1]
            entity2 = st.selectbox("Select Entity 2", remaining_entities, format_func=lambda x: f"{x.id} ({type(x).__name__})")
            
            if st.button("Connect"):
                # Create the connection in the network
                success, message = st.session_state.network.connect(entity1, entity2)
                
                if success:
                    # Store the connection in session state with updated entities
                    # Get fresh copies from session state to ensure we're using the current state
                    if isinstance(entity1, EndDevice):
                        entity1 = st.session_state.devices[entity1.id]
                    else:
                        entity1 = st.session_state.hubs[entity1.id]
                        
                    if isinstance(entity2, EndDevice):
                        entity2 = st.session_state.devices[entity2.id]
                    else:
                        entity2 = st.session_state.hubs[entity2.id]
                    
                    # Add the connection to our list
                    st.session_state.connections.append((entity1, entity2))
                    
                    # Apply connections directly
                    entity1.connect(entity2)
                    entity2.connect(entity1)
                    
                    # Update entities in session state
                    if isinstance(entity1, EndDevice):
                        st.session_state.devices[entity1.id] = entity1
                    else:
                        st.session_state.hubs[entity1.id] = entity1
                        
                    if isinstance(entity2, EndDevice):
                        st.session_state.devices[entity2.id] = entity2
                    else:
                        st.session_state.hubs[entity2.id] = entity2
                        
                    st.success(f"Connected {entity1.id} and {entity2.id}")
                else:
                    st.error(message)
        else:
            st.info("Add at least two entities (devices or hubs) to create connections.")
    
    # Data Transmission
    with st.expander("Send Data", expanded=True):
        devices = list(st.session_state.devices.values())
        if len(devices) >= 2:
            source = st.selectbox("Source Device", devices, format_func=lambda x: x.id)
            dest = st.selectbox("Destination Device", [d for d in devices if d != source], format_func=lambda x: x.id)
            data = st.text_input("Data to send", "Hello, Network!")
            
            if st.button("Send Data"):
                # Make sure we're using current objects
                source = st.session_state.devices[source.id]
                dest = st.session_state.devices[dest.id]
                
                # Find path between source and destination
                path = find_path(source, dest, st.session_state.connections)
                
                if path:
                    # Send data using Physical Layer
                    sent = source.send(data, dest, layer="physical")
                    
                    if sent:
                        # Record the message
                        st.session_state.messages.append({
                            "source": source.id,
                            "destination": dest.id,
                            "data": data,
                            "timestamp": time.strftime("%H:%M:%S"),
                            "path": path
                        })
                        
                        # Highlight the path during data transfer
                        html = visualize_topology(st.session_state.network, st.session_state.connections, highlight_path=path)
                        graph_placeholder.empty()  # Clear the previous graph
                        st.components.v1.html(html, height=500)  # Render the new graph
                        
                        st.success(f"Data sent from {source.id} to {dest.id}")
                    else:
                        st.error(f"Failed to send data to {dest.id}")
                else:
                    st.error(f"No path found between {source.id} and {dest.id}")
        else:
            st.info("Add at least two devices to send data.")

# Create a debug button to restore connections
if st.sidebar.button("Restore Connections"):
    restore_connections()
    st.sidebar.success("Connections restored!")

with col2:
    st.header("Network Topology")
    
    # Initial visualization of the topology
    html = visualize_topology(st.session_state.network, st.session_state.connections)
    graph_placeholder.empty()  # Clear the placeholder
    st.components.v1.html(html, height=500)  # Render the initial graph
    
    # Message history
    with st.expander("Message History", expanded=True):
        if st.session_state.messages:
            for idx, msg in enumerate(reversed(st.session_state.messages)):
                st.write(f"**{msg['timestamp']}**: {msg['source']} → {msg['destination']}")
                st.text(f"Data: {msg['data']}")
                st.text(f"Path: {' → '.join(msg['path'])}")
                if idx < len(st.session_state.messages) - 1:
                    st.divider()
        else:
            st.info("No messages sent yet.")
    
    # Show network information
    with st.expander("Network Information", expanded=True):
        # Display devices
        st.subheader("Devices")
        if st.session_state.devices:
            for device_id, device in st.session_state.devices.items():
                st.write(f"**Device**: {device_id}")
                st.write(f"MAC: {device.mac}")
                
                # Update connected_to display
                connected_to = []
                for conn_entity in device.connected_to:
                    connected_to.append(conn_entity.id)
                
                if connected_to:
                    st.write(f"Connected to: {', '.join(connected_to)}")
                else:
                    st.write("Connected to: None")
                
                # Show received messages
                if device.received_data:
                    st.subheader(f"Received Data ({len(device.received_data)})")
                    for data in device.received_data:
                        st.write(f"From {data['source']}: {data['data']}")
                st.divider()
        else:
            st.info("No devices added yet.")
        
        # Display hubs
        st.subheader("Hubs")
        if st.session_state.hubs:
            for hub_id, hub in st.session_state.hubs.items():
                st.write(f"**Hub**: {hub_id}")
                
                # Update connected_to display
                connected_to = []
                for conn_entity in hub.connected_to:
                    connected_to.append(conn_entity.id)
                
                if connected_to:
                    st.write(f"Connected to: {', '.join(connected_to)}")
                else:
                    st.write("Connected to: None")
                
                st.divider()
        else:
            st.info("No hubs added yet.")

# Add reset button at the bottom
if st.button("Reset Network"):
    for key in ['network', 'devices', 'hubs', 'connections', 'messages']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()