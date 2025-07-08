import networkx as nx
import os
from pyvis.network import Network as PyVisNetwork
from core.devices import EndDevice, Hub, Switch, Bridge, Router
import streamlit as st

def visualize_topology(network, connections, highlight_path=None):
    G = nx.Graph()

    for device in network.devices:
        G.add_node(device.id, label=f"{device.id}", color='#6495ED', 
                  title=f"Device: {device.id}\nMAC: {device.mac}\nIP: {device.ip}\nSubnet Mask: {device.subnet_mask}\nGateway: {device.default_gateway}")
    
    for hub in network.hubs:
        G.add_node(hub.id, label=f"Hub {hub.id}", color='#FF6347', shape='diamond', title=f"Hub: {hub.id}")

    for switch in network.switches:
        G.add_node(switch.id, label=f"Switch {switch.id}", color='#FFD700', shape='square', title=f"Switch: {switch.id}")
        
    for bridge in network.bridges:
        G.add_node(bridge.id, label=f"Bridge {bridge.id}", color='#8A2BE2', shape='triangle', title=f"Bridge: {bridge.id}")
        
    for router in network.routers:
        G.add_node(router.id, label=f"Router {router.id}", color='#FF4500', shape='box', title=f"Router: {router.id}")
        
    for conn in connections:
        if conn[0].id in G.nodes and conn[1].id in G.nodes:  
            G.add_edge(conn[0].id, conn[1].id)
        
    if highlight_path:
        for i in range(len(highlight_path) - 1):
            if G.has_edge(highlight_path[i], highlight_path[i + 1]):
                G.edges[(highlight_path[i], highlight_path[i + 1])]['color'] = '#28A428'
                G.edges[(highlight_path[i], highlight_path[i + 1])]['width'] = 6

    net = PyVisNetwork(height="500px", width="100%", notebook=False)
    net.from_nx(G)
    
    net.toggle_physics(True)
    net.barnes_hut(spring_length=200, spring_strength=0.05)
    
    os.makedirs('temp', exist_ok=True)
    graph_path = "temp/network_graph.html"
    net.save_graph(graph_path)
    
    with open(graph_path, "r", encoding="utf-8") as f:
        html = f.read()
    return html


def find_path(source, destination, connections):
    if not connections:
        return None
        
    G = nx.Graph()
    
    for conn in connections:
        G.add_edge(conn[0].id, conn[1].id)

    try:
        if source.id in G.nodes and destination.id in G.nodes:
            path = nx.shortest_path(G, source=source.id, target=destination.id)
            return path
        return None
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def restore_connections():
    if 'connections' not in st.session_state:
        return
        
    for device in st.session_state.devices.values():
        device.connected_to = []
    for hub in st.session_state.hubs.values():
        hub.connected_to = []
    for switch in st.session_state.switches.values():
        switch.connected_to = []
    for bridge in st.session_state.bridges.values():
        bridge.connected_to = []
    for router in st.session_state.routers.values():
        router.connected_to = []
        router.port_table = {}

    def get_current_entity(entity):
        if isinstance(entity, EndDevice):
            return st.session_state.devices.get(entity.id)
        elif isinstance(entity, Hub):
            return st.session_state.hubs.get(entity.id)
        elif isinstance(entity, Switch):
            return st.session_state.switches.get(entity.id)
        elif isinstance(entity, Bridge):
            return st.session_state.bridges.get(entity.id)
        elif isinstance(entity, Router):
            return st.session_state.routers.get(entity.id)
        return None

    new_connections = []
    for conn in st.session_state.connections:
        entity1, entity2 = conn
        
        current_entity1 = get_current_entity(entity1)
        current_entity2 = get_current_entity(entity2)
        
        if not current_entity1 or not current_entity2:
            continue  
            
        if isinstance(current_entity1, Router) or isinstance(current_entity2, Router):
            router = current_entity1 if isinstance(current_entity1, Router) else current_entity2
            other = current_entity2 if router == current_entity1 else current_entity1
            
            interface_name = None
            if hasattr(router, 'port_table'):
                for device, intf in router.port_table.items():
                    if device.id == other.id:
                        interface_name = intf
                        break
            
            if interface_name:
                success = router.connect(other, interface_name)
            else:
                if router.interfaces:
                    interface_name = next(iter(router.interfaces.keys()))
                    success = router.connect(other, interface_name)
                else:
                    success = False
        else:
            success = current_entity1.connect(current_entity2)
        
        if success:
            new_connections.append((current_entity1, current_entity2))
    
    st.session_state.connections = new_connections

def initialize_session_state(Network):
    if 'network' not in st.session_state:
        st.session_state.network = Network()

    if 'devices' not in st.session_state:
        st.session_state.devices = {}  
    if 'hubs' not in st.session_state:
        st.session_state.hubs = {}  
    if 'switches' not in st.session_state:
        st.session_state.switches = {}  
    if 'bridges' not in st.session_state:
        st.session_state.bridges = {}  
    if 'routers' not in st.session_state:
        st.session_state.routers = {}  

    if 'connections' not in st.session_state:
        st.session_state.connections = []  

    if 'messages' not in st.session_state:
        st.session_state.messages = []  

    if 'selected_layer' not in st.session_state:
        st.session_state.selected_layer = 1