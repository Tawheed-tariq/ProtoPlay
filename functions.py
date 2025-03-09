import networkx as nx
import os
from pyvis.network import Network as PyVisNetwork
from core.devices import EndDevice, Hub, Switch
import streamlit as st

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

    for switch in network.switches:
        G.add_node(switch.id, label=f"Switch {switch.id}", color='#FFD700', shape='square', title=f"Switch: {switch.id}")
        
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
           (isinstance(entity1, Hub) and entity1.id in st.session_state.hubs) or \
           (isinstance(entity1, Switch) and entity1.id in st.session_state.switches):
            if (isinstance(entity2, EndDevice) and entity2.id in st.session_state.devices) or \
               (isinstance(entity2, Hub) and entity2.id in st.session_state.hubs) or \
               (isinstance(entity2, Switch) and entity2.id in st.session_state.switches):
                
                # Get the current instances
                if isinstance(entity1, EndDevice):
                    entity1 = st.session_state.devices[entity1.id]
                elif isinstance(entity1, Switch):
                    entity1 = st.session_state.switches[entity1.id]
                else:
                    entity1 = st.session_state.hubs[entity1.id]
                    
                if isinstance(entity2, EndDevice):
                    entity2 = st.session_state.devices[entity2.id]
                elif isinstance(entity2, Switch):
                    entity2 = st.session_state.switches[entity2.id]
                else:
                    entity2 = st.session_state.hubs[entity2.id]
                
                # Make sure they're connected
                if entity2 not in entity1.connected_to:
                    entity1.connect(entity2)
                if entity1 not in entity2.connected_to:
                    entity2.connect(entity1)
