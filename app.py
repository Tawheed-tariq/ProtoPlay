import streamlit as st
from core.physical import EndDevice, Hub, Network
from core.data_link import Switch, Frame  # Import Data Link Layer classes
import networkx as nx
from pyvis.network import Network as PyVisNetwork
import time

# Initialize network and session state
if 'network' not in st.session_state:
    st.session_state.network = Network()

# Create a placeholder for the graph
graph_placeholder = st.empty()

def visualize_topology(network, highlight_path=None):
    """
    Generate the PyVis graph and return the HTML content.
    """
    G = nx.Graph()
    for device in network.devices:
        G.add_node(device.id, label=f"{device.id}\n{device.mac}", color='blue')
    for hub in network.hubs:
        G.add_node(hub.id, label=f"Hub {hub.id}", color='red')
    for switch in network.switches:
        G.add_node(switch.id, label=f"Switch {switch.id}", color='green')
    for conn in network.connections:
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

def find_path(source, destination, network):
    """
    Find the path between two devices in the network.
    """
    G = nx.Graph()
    for conn in network.connections:
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
                new_device = EndDevice(device_id, mac_address)
                st.session_state.network.add_device(new_device)
                st.success(f"Device {device_id} added with MAC {mac_address}")
            else:
                st.error("Please provide both Device ID and MAC Address.")
    # Add Hub
    with st.form("add_hub"):
        hub_id = st.text_input("Hub ID")
        if st.form_submit_button("Add Hub"):
            if hub_id:
                new_hub = Hub(hub_id)
                st.session_state.network.add_hub(new_hub)
                st.success(f"Hub {hub_id} added")
            else:
                st.error("Please provide a Hub ID.")
    # Add Switch (Data Link Layer)
    if selected_layer == "Data Link Layer":
        with st.form("add_switch"):
            switch_id = st.text_input("Switch ID")
            if st.form_submit_button("Add Switch"):
                if switch_id:
                    new_switch = Switch(switch_id)
                    st.session_state.network.add_switch(new_switch)
                    st.success(f"Switch {switch_id} added")
                else:
                    st.error("Please provide a Switch ID.")

# Connection Management
with st.expander("Create Connections"):
    entities = st.session_state.network.devices + st.session_state.network.hubs
    if selected_layer == "Data Link Layer":
        entities += st.session_state.network.switches

    entity1 = st.selectbox("Select Entity 1", entities, format_func=lambda x: x.id)
    entity2 = st.selectbox("Select Entity 2", entities, format_func=lambda x: x.id)
    
    if st.button("Connect"):
        success, message = st.session_state.network.connect(entity1, entity2)
        if success:
            st.success(message)
        else:
            st.error(message)  
            
# Data Transmission (Physical Layer)
if selected_layer == "Physical Layer":
    with st.expander("Send Data (Physical Layer)"):
        source = st.selectbox("Source Device", st.session_state.network.devices, format_func=lambda x: x.id)
        dest = st.selectbox("Destination Device", st.session_state.network.devices, format_func=lambda x: x.id)
        data = st.text_input("Data")
        if st.button("Send"):
            # Use Physical Layer transmission (raw data)
            path = find_path(source, dest, st.session_state.network)
            if path:
                # Highlight the path during data transfer
                sent = source.send(data, dest, layer="physical")
                if sent:
                    st.success(f"Data sent from {source.id} to {dest.id} via path: {path}")
                    html = visualize_topology(st.session_state.network, highlight_path=path)
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
        source = st.selectbox("Source Device", st.session_state.network.devices, format_func=lambda x: x.id)
        dest = st.selectbox("Destination Device", st.session_state.network.devices, format_func=lambda x: x.id)
        data = st.text_input("Data")
        if st.button("Send Frame"):
            # Use Data Link Layer transmission (frames)
            path = find_path(source, dest, st.session_state.network)
            if path:
                # Highlight the path during data transfer
                html = visualize_topology(st.session_state.network, highlight_path=path)
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
html = visualize_topology(st.session_state.network)
graph_placeholder.empty()  # Clear the placeholder
st.components.v1.html(html, height=450)  # Render the initial graph