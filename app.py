import streamlit as st
from core.physical import EndDevice, Hub, Network
from core.data_link import Switch, Frame  # Import Data Link Layer classes
import networkx as nx
from pyvis.network import Network as PyVisNetwork
import time

# Initialize network and session state
if 'network' not in st.session_state:
    st.session_state.network = Network()

# Store devices, hubs, and switches in session state
if 'devices' not in st.session_state:
    st.session_state.devices = {}  # Store devices by ID
if 'hubs' not in st.session_state:
    st.session_state.hubs = {}  # Store hubs by ID
if 'switches' not in st.session_state:
    st.session_state.switches = {}  # Store switches by ID

# Store connections in session state
if 'connections' not in st.session_state:
    st.session_state.connections = []  # List of connections (entity1, entity2)

# Create a placeholder for the graph
graph_placeholder = st.empty()

def visualize_topology(network, connections, highlight_path=None):
    """
    Generate the PyVis graph and return the HTML content.
    """
    G = nx.Graph()

    # Add all devices, hubs, and switches to the graph
    for device in network.devices:
        G.add_node(device.id, label=f"{device.id}\n{device.mac}", color='blue')
    for hub in network.hubs:
        G.add_node(hub.id, label=f"Hub {hub.id}", color='red')
    for switch in network.switches:
        G.add_node(switch.id, label=f"Switch {switch.id}", color='green')

    # Add all connections to the graph
    for conn in connections:
        G.add_edge(conn[0].id, conn[1].id)
    
    # Highlight the path if data is being transferred
    if highlight_path:
        for i in range(len(highlight_path) - 1):
            G.edges[(highlight_path[i], highlight_path[i + 1])]['color'] = 'green'
            G.edges[(highlight_path[i], highlight_path[i + 1])]['width'] = 3

    # Create a PyVis network
    net = PyVisNetwork(height="400px", width="100%", notebook=False)
    net.from_nx(G)
    net.save_graph("temp.html")
    with open("temp.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html

def find_path(source, destination, network, connections=st.session_state.connections):
    """
    Find the path between two devices in the network.
    """
    G = nx.Graph()

    # Add all devices, hubs, and switches to the graph
    for device in network.devices:
        G.add_node(device.id)
    for hub in network.hubs:
        G.add_node(hub.id)
    for switch in network.switches:
        G.add_node(switch.id)

    # Add all connections to the graph
    for conn in connections:
        G.add_edge(conn[0].id, conn[1].id)

    try:
        path = nx.shortest_path(G, source=source.id, target=destination.id)
        return path
    except nx.NetworkXNoPath:
        return None

# Streamlit UI
st.title("Network Simulator")

# Sidebar: Layer Selection
with st.sidebar:
    st.header("Layer Selection")
    selected_layer = st.selectbox(
        "Select Layer",
        ["Physical Layer", "Data Link Layer"],
        key="layer_selection"
    )

# Sidebar: Add devices/hubs/switches
with st.sidebar:
    st.header("Add Entities")
    # Add End Device
    with st.form("add_device"):
        device_id = st.text_input("Device ID")
        mac_address = st.text_input("MAC Address (format: XX:XX:XX:XX:XX:XX)")
        if st.form_submit_button("Add Device"):
            if mac_address and device_id:
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
        hub_id = st.text_input("Hub ID")
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
    # Add Switch (Data Link Layer)
    if selected_layer == "Data Link Layer":
        with st.form("add_switch"):
            switch_id = st.text_input("Switch ID")
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

# Connection Management
with st.expander("Create Connections"):
    entities = list(st.session_state.devices.values()) + list(st.session_state.hubs.values())
    if selected_layer == "Data Link Layer":
        entities += list(st.session_state.switches.values())

    entity1 = st.selectbox("Select Entity 1", entities, format_func=lambda x: x.id)
    entity2 = st.selectbox("Select Entity 2", entities, format_func=lambda x: x.id)
    
    if st.button("Connect"):
        # Update connected_to attributes
        entity1.connected_to = entity2
        entity2.connected_to = entity1

        # Store the connection in session state
        st.session_state.connections.append((entity1, entity2))

        # Update the objects in session state
        if isinstance(entity1, EndDevice):
            st.session_state.devices[entity1.id] = entity1
        elif isinstance(entity1, Hub):
            st.session_state.hubs[entity1.id] = entity1
        elif isinstance(entity1, Switch):
            st.session_state.switches[entity1.id] = entity1

        if isinstance(entity2, EndDevice):
            st.session_state.devices[entity2.id] = entity2
        elif isinstance(entity2, Hub):
            st.session_state.hubs[entity2.id] = entity2
        elif isinstance(entity2, Switch):
            st.session_state.switches[entity2.id] = entity2

        st.success(f"Connected {entity1.id} and {entity2.id}")

# Restore connections from session state
for conn in st.session_state.connections:
    entity1, entity2 = conn
    entity1.connected_to = entity2
    entity2.connected_to = entity1

    # Update the objects in session state
    if isinstance(entity1, EndDevice):
        st.session_state.devices[entity1.id] = entity1
    elif isinstance(entity1, Hub):
        st.session_state.hubs[entity1.id] = entity1
    elif isinstance(entity1, Switch):
        st.session_state.switches[entity1.id] = entity1

    if isinstance(entity2, EndDevice):
        st.session_state.devices[entity2.id] = entity2
    elif isinstance(entity2, Hub):
        st.session_state.hubs[entity2.id] = entity2
    elif isinstance(entity2, Switch):
        st.session_state.switches[entity2.id] = entity2

# Data Transmission (Physical Layer)
if selected_layer == "Physical Layer":
    with st.expander("Send Data (Physical Layer)"):
        # Fetch devices from session state
        devices = list(st.session_state.devices.values())
        source = st.selectbox("Source Device", devices, format_func=lambda x: x.id)
        dest = st.selectbox("Destination Device", devices, format_func=lambda x: x.id)
        data = st.text_input("Data")
        if st.button("Send"):
            # Fetch the latest state of source and destination
            source = st.session_state.devices[source.id]
            dest = st.session_state.devices[dest.id]

            # Debug: Check the state of source.connected_to
            st.write(f"Debug: Source {source.id} connected_to = {source.connected_to}")
            st.write(f"Debug: Destination {dest.id} connected_to = {dest.connected_to}")

            # Use Physical Layer transmission (raw data)
            path = find_path(source, dest, st.session_state.network)
            if path:
                # Highlight the path during data transfer
                sent = source.send(data, dest, layer="physical")
                if sent:
                    st.success(f"Data sent from {source.id} to {dest.id} via path: {path}")
                    html = visualize_topology(st.session_state.network,st.session_state.connections, highlight_path=path)
                    graph_placeholder.empty()  # Clear the previous graph
                    st.components.v1.html(html, height=450)  # Render the new graph
                else:
                    st.error(f"Destination {dest.id} not connected to the network")
            else:
                st.error(f"No path found between {source.id} and {dest.id}")

# Data Link Layer Functionality
elif selected_layer == "Data Link Layer":
    with st.expander("Data Link Layer Functionality"):
        st.write("### MAC Learning and Forwarding")
        # Add a button to send frames (Data Link Layer)
        devices = list(st.session_state.devices.values())
        source = st.selectbox("Source Device", devices, format_func=lambda x: x.id)
        dest = st.selectbox("Destination Device", devices, format_func=lambda x: x.id)
        data = st.text_input("Data")
        if st.button("Send Frame"):
            # Use Data Link Layer transmission (frames)
            path = find_path(source, dest, st.session_state.network)
            if path:
                # Highlight the path during data transfer
                html = visualize_topology(st.session_state.network, st.session_state.connections, highlight_path=path)
                graph_placeholder.empty()  # Clear the previous graph
                st.components.v1.html(html, height=450)  # Render the new graph
                st.success(f"Frame sent from {source.id} to {dest.id} via path: {path}")
                # Simulate data transfer delay
                time.sleep(1)  # Simulate a delay for visualization
                source.send(data, dest, layer="data_link")
            else:
                st.error(f"No path found between {source.id} and {dest.id}")

        if st.button("Show MAC Table"):
            for switch in st.session_state.network.switches:
                st.write(f"Switch {switch.id} MAC Table:")
                st.write(switch.mac_table)  # Now this will show entries!

# Initial visualization of the topology
html = visualize_topology(st.session_state.network, st.session_state.connections)
graph_placeholder.empty()  # Clear the placeholder
st.components.v1.html(html, height=450)  # Render the initial graph