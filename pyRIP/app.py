import streamlit as st
import json
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import random
import sys
import os
import socket

# Import the RIP implementation
from pyrip_lib import *
from pyrip import RipPacket, RipRoute, IP2Int, Int2IP, PrefixLen2MaskInt, MaskInt2PrefixLen

# Import from the provided libraries
#from pyrip_lib import *
#from pyrip import RipPacket, RipRoute, IRoute

# Configure page layout
st.set_page_config(
    page_title="RIP Protocol Simulator",
    page_icon="🌐",
    layout="wide",
)

# Initialize session state
if 'rib' not in st.session_state:
    st.session_state.rib = []
if 'routes_history' not in st.session_state:
    st.session_state.routes_history = []
if 'packets_sent' not in st.session_state:
    st.session_state.packets_sent = []
if 'packets_received' not in st.session_state:
    st.session_state.packets_received = []
if 'config' not in st.session_state:
    st.session_state.config = {
        "updateTime": RIP_DEFAULT_UPDATE,
        "timeoutTime": RIP_DEFAULT_TIMEOUT,
        "garbageTime": RIP_DEFAULT_GARBAGE,
        "routes": []
    }

# Title and description
st.title("RIP Protocol Simulator")
st.markdown("""
This application simulates the Routing Information Protocol (RIPv2) operation. 
It allows you to visualize the routing table, configure routes, and simulate packet exchanges.
""")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Routing Table", "Network Visualization", "Packet Simulator", "Configuration"])

# Tab 1: Routing Table
with tab1:
    st.header("Routing Information Base (RIB)")
    
    # Add new route form
    with st.expander("Add New Route"):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            prefix = st.text_input("Prefix", "192.168.1.0")
        with col2:
            prefix_len = st.number_input("Prefix Length", min_value=0, max_value=32, value=24)
        with col3:
            next_hop = st.text_input("Next Hop", "10.0.0.1")
        with col4:
            metric = st.number_input("Metric", min_value=1, max_value=16, value=1)
        with col5:
            route_tag = st.number_input("Route Tag", min_value=0, value=0)
        
        if st.button("Add Route"):
            # Create new route and add to RIB
            new_route = RipRoute(
                IP2Int(prefix),
                prefix_len,
                IP2Int(next_hop),
                metric,
                route_tag
            )
            # Add timer-like attributes
            new_route.timeoutTimer = time.time() + st.session_state.config["timeoutTime"]
            new_route.garbageTimer = None
            
            # Check if route already exists
            exists = False
            for r in st.session_state.rib:
                if r.prefix == new_route.prefix and r.prefixLen == new_route.prefixLen:
                    exists = True
                    break
            
            if not exists:
                st.session_state.rib.append(new_route)
                st.session_state.routes_history.append({
                    "time": time.strftime("%H:%M:%S"),
                    "action": "Added",
                    "prefix": prefix,
                    "prefixLen": prefix_len,
                    "nextHop": next_hop,
                    "metric": metric
                })
                st.success(f"Route {prefix}/{prefix_len} added successfully!")
            else:
                st.error(f"Route {prefix}/{prefix_len} already exists!")
    
    # Display Routing Table
    if st.session_state.rib:
        data = []
        for route in st.session_state.rib:
            timeout = route.timeoutTimer - time.time() if hasattr(route, 'timeoutTimer') and route.timeoutTimer else -1
            garbage = route.garbageTimer - time.time() if hasattr(route, 'garbageTimer') and route.garbageTimer else -1
            
            data.append({
                "Destination": f"{Int2IP(route.prefix)}/{route.prefixLen}",
                "Next Hop": Int2IP(route.nextHop),
                "Metric": route.metric,
                "Route Tag": route.routeTag,
                "Timeout": f"{int(timeout)}s" if timeout > 0 else "N/A",
                "Garbage": f"{int(garbage)}s" if garbage > 0 else "N/A"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Option to delete routes
        if st.button("Clear All Routes"):
            st.session_state.rib = []
            st.session_state.routes_history.append({
                "time": time.strftime("%H:%M:%S"),
                "action": "Cleared",
                "prefix": "ALL",
                "prefixLen": "",
                "nextHop": "",
                "metric": ""
            })
            st.success("All routes cleared!")
    else:
        st.info("No routes in the routing table. Add routes using the form above.")
    
    # Route Query
    st.header("Route Lookup")
    ip_to_lookup = st.text_input("Enter IP address to lookup", "192.168.1.10")
    if st.button("Lookup"):
        ip_int = IP2Int(ip_to_lookup)
        best_route = None
        best_prefix_len = -1
        
        for route in st.session_state.rib:
            mask = PrefixLen2MaskInt(route.prefixLen)
            if (ip_int & mask) == (route.prefix & mask):
                if route.prefixLen > best_prefix_len:
                    best_prefix_len = route.prefixLen
                    best_route = route
                elif route.prefixLen == best_prefix_len:
                    if best_route and route.metric < best_route.metric:
                        best_route = route
        
        if best_route:
            st.success(f"Best route for {ip_to_lookup} is via {Int2IP(best_route.nextHop)} with metric {best_route.metric}")
        else:
            st.error(f"No route found for {ip_to_lookup}")

# Tab 2: Network Visualization
with tab2:
    st.header("Network Topology")
    
    if st.session_state.rib:
        # Create a graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        router_node = "This Router"
        G.add_node(router_node)
        
        # Group routes by next hop
        next_hops = {}
        for route in st.session_state.rib:
            next_hop = Int2IP(route.nextHop)
            dest_net = f"{Int2IP(route.prefix)}/{route.prefixLen}"
            
            if next_hop not in next_hops:
                next_hops[next_hop] = []
                G.add_node(next_hop)
                G.add_edge(router_node, next_hop, weight=1)
            
            next_hops[next_hop].append(dest_net)
            G.add_node(dest_net)
            G.add_edge(next_hop, dest_net, weight=route.metric)
        
        # Draw the graph
        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.kamada_kawai_layout(G)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color="skyblue", alpha=0.8)
        nx.draw_networkx_nodes(G, pos, nodelist=[router_node], node_size=1000, node_color="red", alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrowsize=20)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")
        
        # Edge labels
        edge_labels = {(u, v): f"metric: {d['weight']}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        # Display the plot
        st.pyplot(fig)
    else:
        st.info("No routes available for visualization. Add routes to see the network topology.")

# Tab 3: Packet Simulator
with tab3:
    st.header("RIP Packet Simulator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Send RIP Packet")
        packet_type = st.radio("Packet Type", ["Request", "Response"])
        
        if packet_type == "Request":
            request_type = st.radio("Request Type", ["All Routes", "Specific Route"])
            
            if request_type == "Specific Route":
                req_prefix = st.text_input("Request Prefix", "192.168.1.0")
                req_prefix_len = st.number_input("Request Prefix Length", min_value=0, max_value=32, value=24)
            
            if st.button("Send Request"):
                pkt = RipPacket(RIP_COMMAND_REQUEST, 2)
                
                if request_type == "All Routes":
                    pkt.addEntry(0, 0, 0, RIP_METRIC_INFINITY, 0, 0)
                    st.session_state.packets_sent.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": "Request (All Routes)",
                        "content": "Request for all routes"
                    })
                else:
                    pkt.addEntry(IP2Int(req_prefix), req_prefix_len, 0, RIP_METRIC_INFINITY)
                    st.session_state.packets_sent.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": f"Request (Specific Route)",
                        "content": f"Request for {req_prefix}/{req_prefix_len}"
                    })
                
                st.success(f"Request packet sent: {pkt}")
                
                # Simulate receiving a response
                if st.session_state.rib:
                    resp_pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
                    
                    if request_type == "All Routes":
                        for r in st.session_state.rib:
                            resp_pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric, r.routeTag)
                    else:
                        for r in st.session_state.rib:
                            if r.prefix == IP2Int(req_prefix) and r.prefixLen == req_prefix_len:
                                resp_pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric, r.routeTag)
                    
                    if resp_pkt.entry:
                        st.session_state.packets_received.append({
                            "time": time.strftime("%H:%M:%S"),
                            "type": "Response",
                            "content": f"Response with {len(resp_pkt.entry)} routes"
                        })
        
        else:  # Response
            dest_addr = st.text_input("Destination Address", "224.0.0.9")
            
            if st.button("Send Response"):
                pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
                
                for r in st.session_state.rib:
                    if r.metric < RIP_METRIC_MAX:
                        pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric, r.routeTag)
                
                if pkt.entry:
                    st.session_state.packets_sent.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": "Response",
                        "content": f"Regular update with {len(pkt.entry)} routes"
                    })
                    st.success(f"Response packet sent: {pkt}")
                else:
                    st.warning("No valid routes to include in response packet.")
    
    with col2:
        st.subheader("Simulate Received Packet")
        sim_packet_type = st.radio("Simulate Packet Type", ["Request", "Response"], key="sim_packet_type")
        src_addr = st.text_input("Source Address", "192.168.1.1")
        
        if sim_packet_type == "Request":
            sim_request_type = st.radio("Simulate Request Type", ["All Routes", "Specific Route"])
            
            if sim_request_type == "Specific Route":
                sim_req_prefix = st.text_input("Request Prefix", "192.168.1.0", key="sim_req_prefix")
                sim_req_prefix_len = st.number_input("Request Prefix Length", min_value=0, max_value=32, value=24, key="sim_req_prefix_len")
            
            if st.button("Simulate Received Request"):
                pkt = RipPacket(RIP_COMMAND_REQUEST, 2)
                
                if sim_request_type == "All Routes":
                    pkt.addEntry(0, 0, 0, RIP_METRIC_INFINITY, 0, 0)
                    st.session_state.packets_received.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": "Request (All Routes)",
                        "content": f"Request from {src_addr} for all routes"
                    })
                else:
                    pkt.addEntry(IP2Int(sim_req_prefix), sim_req_prefix_len, 0, RIP_METRIC_INFINITY)
                    st.session_state.packets_received.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": f"Request (Specific Route)",
                        "content": f"Request from {src_addr} for {sim_req_prefix}/{sim_req_prefix_len}"
                    })
                
                st.success(f"Simulated received request: {pkt}")
                
                # Create response
                resp_pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
                
                if sim_request_type == "All Routes":
                    for r in st.session_state.rib:
                        resp_pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric, r.routeTag)
                else:
                    for r in st.session_state.rib:
                        if r.prefix == IP2Int(sim_req_prefix) and r.prefixLen == sim_req_prefix_len:
                            resp_pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric, r.routeTag)
                
                if resp_pkt.entry:
                    st.session_state.packets_sent.append({
                        "time": time.strftime("%H:%M:%S"),
                        "type": "Response",
                        "content": f"Response to {src_addr} with {len(resp_pkt.entry)} routes"
                    })
                    st.info(f"Sent response: {resp_pkt}")
        
        else:  # Response
            st.subheader("Simulate Route Reception")
            sim_resp_prefix = st.text_input("Prefix", "192.168.2.0")
            sim_resp_prefix_len = st.number_input("Prefix Length", min_value=0, max_value=32, value=24)
            sim_resp_next_hop = st.text_input("Next Hop", src_addr)
            sim_resp_metric = st.number_input("Metric", min_value=1, max_value=16, value=2)
            
            if st.button("Simulate Received Route"):
                # Create a response packet with the route
                pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
                pkt.addEntry(
                    IP2Int(sim_resp_prefix),
                    sim_resp_prefix_len,
                    IP2Int(sim_resp_next_hop),
                    sim_resp_metric
                )
                
                st.session_state.packets_received.append({
                    "time": time.strftime("%H:%M:%S"),
                    "type": "Response",
                    "content": f"Route update from {src_addr}: {sim_resp_prefix}/{sim_resp_prefix_len} via {sim_resp_next_hop} metric {sim_resp_metric}"
                })
                
                st.success(f"Simulated received response: {pkt}")
                
                # Update RIB
                new_route = RipRoute(
                    IP2Int(sim_resp_prefix),
                    sim_resp_prefix_len,
                    IP2Int(sim_resp_next_hop),
                    sim_resp_metric
                )
                
                # Add timer-like attributes
                new_route.timeoutTimer = time.time() + st.session_state.config["timeoutTime"]
                new_route.garbageTimer = None
                
                # Check if route already exists
                exists = False
                updated = False
                for i, r in enumerate(st.session_state.rib):
                    if r.prefix == new_route.prefix and r.prefixLen == new_route.prefixLen:
                        exists = True
                        # Update if metric is better or next hop differs
                        if new_route.metric < r.metric or new_route.nextHop != r.nextHop:
                            st.session_state.rib[i] = new_route
                            updated = True
                            st.session_state.routes_history.append({
                                "time": time.strftime("%H:%M:%S"),
                                "action": "Updated",
                                "prefix": sim_resp_prefix,
                                "prefixLen": sim_resp_prefix_len,
                                "nextHop": sim_resp_next_hop,
                                "metric": sim_resp_metric
                            })
                        break
                
                if not exists:
                    st.session_state.rib.append(new_route)
                    st.session_state.routes_history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "action": "Added",
                        "prefix": sim_resp_prefix,
                        "prefixLen": sim_resp_prefix_len,
                        "nextHop": sim_resp_next_hop,
                        "metric": sim_resp_metric
                    })
                    st.info(f"Route {sim_resp_prefix}/{sim_resp_prefix_len} added to RIB")
                elif updated:
                    st.info(f"Route {sim_resp_prefix}/{sim_resp_prefix_len} updated in RIB")
                else:
                    st.info(f"Route {sim_resp_prefix}/{sim_resp_prefix_len} already exists with equal or better metric")

    # Display packet history
    st.subheader("Packet History")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sent Packets")
        if st.session_state.packets_sent:
            sent_df = pd.DataFrame(st.session_state.packets_sent)
            st.dataframe(sent_df, use_container_width=True, hide_index=True)
        else:
            st.info("No packets sent yet.")
    
    with col2:
        st.subheader("Received Packets")
        if st.session_state.packets_received:
            recv_df = pd.DataFrame(st.session_state.packets_received)
            st.dataframe(recv_df, use_container_width=True, hide_index=True)
        else:
            st.info("No packets received yet.")

# Tab 4: Configuration
with tab4:
    st.header("RIP Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        update_time = st.number_input("Update Time (seconds)", 
                                     min_value=1, 
                                     value=st.session_state.config["updateTime"],
                                     help="Time between regular routing updates")
    
    with col2:
        timeout_time = st.number_input("Timeout Time (seconds)", 
                                      min_value=1, 
                                      value=st.session_state.config["timeoutTime"],
                                      help="Time after which a route is considered invalid if no updates received")
    
    with col3:
        garbage_time = st.number_input("Garbage Collection Time (seconds)", 
                                      min_value=1, 
                                      value=st.session_state.config["garbageTime"],
                                      help="Time before an invalid route is removed from the routing table")
    
    if st.button("Save Configuration"):
        st.session_state.config["updateTime"] = update_time
        st.session_state.config["timeoutTime"] = timeout_time
        st.session_state.config["garbageTime"] = garbage_time
        st.success("Configuration saved successfully!")
    
    # Export/Import configuration
    st.subheader("Import/Export Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Configuration"):
            # Create config JSON with current routes
            config = {
                "updateTime": st.session_state.config["updateTime"],
                "timeoutTime": st.session_state.config["timeoutTime"],
                "garbageTime": st.session_state.config["garbageTime"],
                "routes": []
            }
            
            for route in st.session_state.rib:
                config["routes"].append({
                    "prefix": Int2IP(route.prefix),
                    "prefixLen": route.prefixLen,
                    "nextHop": Int2IP(route.nextHop),
                    "metric": route.metric,
                    "routeTag": route.routeTag
                })
            
            st.download_button(
                label="Download Configuration",
                data=json.dumps(config, indent=2),
                file_name="rip_config.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("Upload Configuration", type=["json"])
        if uploaded_file is not None:
            try:
                config = json.load(uploaded_file)
                
                # Update config parameters
                if "updateTime" in config:
                    st.session_state.config["updateTime"] = config["updateTime"]
                if "timeoutTime" in config:
                    st.session_state.config["timeoutTime"] = config["timeoutTime"]
                if "garbageTime" in config:
                    st.session_state.config["garbageTime"] = config["garbageTime"]
                
                # Clear existing routes
                st.session_state.rib = []
                
                # Add imported routes
                if "routes" in config:
                    for r in config["routes"]:
                        if set(("prefix", "prefixLen", "nextHop")) <= set(r.keys()):
                            new_route = RipRoute(
                                IP2Int(r["prefix"]),
                                r["prefixLen"],
                                IP2Int(r["nextHop"]),
                                r.get("metric", RIP_METRIC_MIN),
                                r.get("routeTag", 0)
                            )
                            # Add timer-like attributes
                            new_route.timeoutTimer = time.time() + st.session_state.config["timeoutTime"]
                            new_route.garbageTimer = None
                            st.session_state.rib.append(new_route)
                
                st.success(f"Configuration imported successfully with {len(st.session_state.rib)} routes!")
                
            except Exception as e:
                st.error(f"Error importing configuration: {str(e)}")
    
    # Show route modification history
    st.subheader("Route Modification History")
    if st.session_state.routes_history:
        history_df = pd.DataFrame(st.session_state.routes_history)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No route modifications recorded yet.")

# Sidebar for timer simulation
with st.sidebar:
    st.header("Timer Simulation")
    
    if st.button("Simulate Timer Tick"):
        # Decrease timeout timers
        for route in st.session_state.rib:
            if hasattr(route, 'timeoutTimer') and route.timeoutTimer is not None:
                # If timeout expired
                if route.timeoutTimer <= time.time():
                    route.timeoutTimer = None
                    route.metric = RIP_METRIC_INFINITY
                    route.garbageTimer = time.time() + st.session_state.config["garbageTime"]
                    
                    st.session_state.routes_history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "action": "Timeout",
                        "prefix": Int2IP(route.prefix),
                        "prefixLen": route.prefixLen,
                        "nextHop": Int2IP(route.nextHop),
                        "metric": RIP_METRIC_INFINITY
                    })
            
            # If garbage collection timer expired
            if hasattr(route, 'garbageTimer') and route.garbageTimer is not None:
                if route.garbageTimer <= time.time():
                    # Mark for deletion
                    st.session_state.routes_history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "action": "Deleted",
                        "prefix": Int2IP(route.prefix),
                        "prefixLen": route.prefixLen,
                        "nextHop": Int2IP(route.nextHop),
                        "metric": route.metric
                    })
        
        # Remove expired routes
        st.session_state.rib = [r for r in st.session_state.rib 
                                if not (hasattr(r, 'garbageTimer') and r.garbageTimer is not None and r.garbageTimer <= time.time())]
        
        st.success("Timer tick simulated!")
    
    if st.button("Send Update Packet"):
        pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
        for r in st.session_state.rib:
            if r.metric < RIP_METRIC_MAX:
                pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric)
        
        if pkt.entry:
            st.session_state.packets_sent.append({
                "time": time.strftime("%H:%M:%S"),
                "type": "Response",
                "content": f"Regular update with {len(pkt.entry)} routes"
            })
            st.success(f"Update packet sent with {len(pkt.entry)} routes!")
        else:
            st.warning("No valid routes to include in update packet.")
    
    # About section
    st.markdown("---")
    st.subheader("About RIP Protocol")
    st.markdown("""
    **RIP (Routing Information Protocol)** is a distance-vector routing protocol that uses hop count as a routing metric. 
    
    **Key characteristics:**
    - Maximum hop count: 15 (16 is considered infinity)
    - Uses distance-vector algorithm
    - Updates every 30 seconds (configurable)
    - Uses route timeout and garbage collection
    - Supports split horizon and poison reverse
    
    This simulator implements RIPv2 which adds support for CIDR and authentication.
    """)

# Quick help section
st.sidebar.markdown("---")
st.sidebar.subheader("Quick Help")
st.sidebar.markdown("""
- **Routing Table**: View and manage routes
- **Network Visualization**: See network topology
- **Packet Simulator**: Simulate RIP packet exchange
- **Configuration**: Set RIP parameters
- **Timer Simulation**: Simulate timeouts and updates
""")