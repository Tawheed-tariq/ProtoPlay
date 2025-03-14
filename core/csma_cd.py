import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import time
from collections import deque
import numpy as np
import pandas as pd

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.backoff_counter = 0
        self.max_backoff_attempts = 10
        self.transmission_queue = deque()
        self.current_packet = None
        self.state = "IDLE"  # IDLE, SENSING, TRANSMITTING, BACKOFF
        self.collision_count = 0
        self.successful_transmissions = 0
        self.color = "blue"
        self.transmission_start_time = 0
        self.transmission_attempts = 0

    def generate_packet(self, destination, size):
        """Generate a new packet and add it to the transmission queue"""
        packet = {
            "source": self.node_id,
            "destination": destination,
            "size": size,
            "created_time": time.time(),
            "id": random.randint(1, 1000)
        }
        self.transmission_queue.append(packet)
        return packet

    def sense_channel(self, network):
        """Check if the channel is free"""
        return network.channel_state == "FREE"

    def start_transmission(self, network):
        """Start transmitting a packet"""
        if self.transmission_queue:
            self.current_packet = self.transmission_queue.popleft()
            self.state = "TRANSMITTING"
            network.channel_state = "BUSY"
            network.current_transmitters.append(self)
            self.color = "red"
            self.transmission_start_time = network.current_time
            self.transmission_attempts += 1
            return True
        return False

    def handle_collision(self):
        """Handle collision using binary exponential backoff"""
        self.collision_count += 1
        self.state = "BACKOFF"
        if self.collision_count > self.max_backoff_attempts:
            # Discard packet after too many attempts
            self.current_packet = None
            self.collision_count = 0
            self.state = "IDLE"
            self.color = "blue"
        else:
            # Calculate backoff time using binary exponential backoff
            max_backoff = 2 ** min(self.collision_count, 10)
            self.backoff_counter = random.randint(0, max_backoff - 1)
            self.color = "orange"

    def update(self, network):
        """Update node state in each time step"""
        if self.state == "IDLE" and self.transmission_queue:
            self.state = "SENSING"
            self.color = "yellow"
        
        elif self.state == "SENSING":
            if self.sense_channel(network):
                self.start_transmission(network)
            
        elif self.state == "BACKOFF":
            self.backoff_counter -= 1
            if self.backoff_counter <= 0:
                self.state = "SENSING"
                self.color = "yellow"
                
        # If transmitting, network will handle transmission progress
        
        return self.state


class Network:
    def __init__(self, num_nodes=5, collision_probability=0.1):
        self.nodes = [Node(i) for i in range(num_nodes)]
        self.channel_state = "FREE"
        self.current_transmitters = []
        self.transmission_progress = 0
        self.transmission_duration = 12  # time steps to complete transmission
        self.collision_detected = False
        self.collision_probability = collision_probability  # Probability of additional collision
        self.G = nx.Graph()
        self.setup_network_graph()
        self.history = []  # To track events for visualization
        self.current_time = 0
        self.collision_events = []  # To track collision events for visualization
        self.collision_count = 0
        self.successful_transmissions = 0
        self.collision_rate = 0
        self.metrics_history = []
        
    def setup_network_graph(self):
        """Set up the network graph for visualization"""
        # Create a bus topology
        for i in range(len(self.nodes)):
            self.G.add_node(i, pos=(i, 0))
            
        # Add edges to represent the bus
        for i in range(len(self.nodes) - 1):
            self.G.add_edge(i, i + 1)
    
    def update(self):
        """Update the network state"""
        self.current_time += 1
        
        for node in self.nodes:
            node.update(self)
        
        if (self.current_transmitters and len(self.current_transmitters) == 1 and 
            random.random() < self.collision_probability):
            
            # if any node is sensing we set it to transmit state
            sensing_nodes = [node for node in self.nodes if node.state == "SENSING"]
            
            if sensing_nodes:
                # let the collision happen
                force_node = random.choice(sensing_nodes)
                force_node.start_transmission(self)
                self.history.append(f"collision: Node {force_node.node_id} started transmission")
        
        # handle transmissions
        if self.current_transmitters:
            if len(self.current_transmitters) > 1:
                self.handle_collision()
            else:
                self.transmission_progress += 1
                
                if self.transmission_progress >= self.transmission_duration:
                    node = self.current_transmitters[0]
                    self.history.append(f"Node {node.node_id} successfully transmitted packet {node.current_packet['id']} to Node {node.current_packet['destination']}")
                    node.successful_transmissions += 1
                    self.successful_transmissions += 1
                    node.current_packet = None
                    node.state = "IDLE"
                    node.color = "blue"
                    node.collision_count = 0
                    self.current_transmitters = []
                    self.transmission_progress = 0
                    self.channel_state = "FREE"
        
        total_attempts = self.collision_count + self.successful_transmissions
        self.collision_rate = self.collision_count / max(1, total_attempts)
        
        self.metrics_history.append({
            "time": self.current_time,
            "collisions": self.collision_count,
            "successful_transmissions": self.successful_transmissions,
            "collision_rate": self.collision_rate
        })
    
    def handle_collision(self):
        """Handle collision on the network"""
        self.collision_count += 1
        involved_nodes = [node.node_id for node in self.current_transmitters]
        self.history.append(f"Collision detected between nodes {involved_nodes}")
        self.collision_detected = True
        
        self.collision_events.append({
            "time": self.current_time,
            "nodes": involved_nodes,
            "display_until": self.current_time + 5  # Display collision for 5 time steps
        })
        
        # Each node handles its own collision
        for node in self.current_transmitters:
            node.handle_collision()
        
        # Reset network state
        self.current_transmitters = []
        self.transmission_progress = 0
        self.channel_state = "FREE"
        self.collision_detected = False

    def generate_random_traffic(self, probability=0.1):
        """Generate random traffic in the network"""
        for node in self.nodes:
            if node.state == "IDLE" and random.random() < probability:
                dest = random.choice([n for n in range(len(self.nodes)) if n != node.node_id])
                size = random.randint(1, 10)
                packet = node.generate_packet(dest, size)
                self.history.append(f"Node {node.node_id} generated packet {packet['id']} for Node {dest}")

    def visualize(self):
        """Visualize the network state"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # Network visualization
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Draw edges
        nx.draw_networkx_edges(self.G, pos, width=2.0, alpha=0.5, ax=ax1)
        
        # Draw nodes with colors based on state
        node_colors = [self.nodes[i].color for i in range(len(self.nodes))]
        nx.draw_networkx_nodes(self.G, pos, node_color=node_colors, node_size=500, ax=ax1)
        
        # Draw labels
        labels = {i: f"{i}\n{self.nodes[i].state}" for i in range(len(self.nodes))}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax1)
        
        # Visualize active collisions
        active_collisions = [c for c in self.collision_events if c["display_until"] >= self.current_time]
        for collision in active_collisions:
            for node_id in collision["nodes"]:
                # Draw a red lightning bolt or explosion to represent collision
                node_pos = pos[node_id]
                circle = plt.Circle(node_pos, 0.3, color='red', alpha=0.5, fill=True)
                ax1.add_patch(circle)
                ax1.text(node_pos[0], node_pos[1]-0.2, "***", fontsize=20, color='red', 
                        ha='center', va='center')
    
        
        # Add a title
        ax1.set_title("CSMA/CD Network Simulation")
        ax1.axis('off')
        
        # Plot collision rate over time
        if len(self.metrics_history) > 1:
            times = [m["time"] for m in self.metrics_history]
            collision_rates = [m["collision_rate"] for m in self.metrics_history]
            
            ax2.plot(times, collision_rates, 'r-', label='Collision Rate')
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Collision Rate')
            ax2.set_title('Network Collision Rate Over Time')
            ax2.grid(True)
            ax2.legend()
            
            # Add current collision rate as text
            current_rate = self.collision_rate
            ax2.text(0.95, 0.95, f"Current Collision Rate: {current_rate:.2f}", 
                     transform=ax2.transAxes, verticalalignment='top', 
                     horizontalalignment='right',
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
        
        plt.tight_layout()
        return fig

    def get_collision_statistics(self):
        """Get collision statistics for display"""
        stats = {
            "Total Collisions": self.collision_count,
            "Successful Transmissions": self.successful_transmissions,
            "Current Collision Rate": f"{self.collision_rate:.2f}",
            "Channel State": self.channel_state
        }
        return stats


def csmaCD():
    st.title("CSMA/CD Protocol Simulation")
    
    st.markdown("""
    ### Node States
    - **IDLE (Blue)**: Node is Idle (not transmitting). 
    - **SENSING (Yellow)**: Node is checking if the channel is free.
    - **TRANSMITTING (Red)**: Node is sending data
    - **BACKOFF (Orange)**: Node is waiting after a collision
    
    ### Collision Visualization
    - Red *** shows active collisions
    - Collision rate graph shows how frequently collisions occur over time
    """)
    
    st.header("Simulation Parameters")
    num_nodes = st.slider("Number of Nodes", 3, 10, 5)
    traffic_rate = st.slider("Traffic Generation Rate", 0.01, 0.3, 0.1)
    collision_probability = st.slider("Collision Probability", 0.0, 0.5, 0.1, 
                                             help="Probability of forcing additional collisions")
    simulation_speed = st.slider("Simulation Speed", 1, 10, 3)
    
    # Initialize the network
    if 'network_csma' not in st.session_state:
        st.session_state.network_csma = Network(num_nodes, collision_probability)
        st.session_state.step = 0
    
    # Reset button
    if st.button("Reset Simulation"):
        st.session_state.network_csma = Network(num_nodes, collision_probability)
        st.session_state.step = 0
    
    # Update collision probability if changed
    if hasattr(st.session_state, 'network_csma'):
        st.session_state.network_csma.collision_probability = collision_probability
    
    # Create placeholders for visualization
    vis_placeholder = st.empty()
    # stats_placeholder = st.empty()
    
    col1, col2 = st.columns(2)
    collision_stats_placeholder = col1.empty()
    node_stats_placeholder = col2.empty()
    
    history_placeholder = st.empty()
    
    if st.button("Run Simulation Step"):
        # Update network state
        st.session_state.network_csma.generate_random_traffic(traffic_rate)
        st.session_state.network_csma.update()
        st.session_state.step += 1
        
        # Update visualization
        fig = st.session_state.network_csma.visualize()
        vis_placeholder.pyplot(fig)
        plt.close()
        
        collision_stats = st.session_state.network_csma.get_collision_statistics()
        collision_stats_placeholder.subheader("Network Statistics")
        collision_stats_placeholder.json(collision_stats)
        
        stats_df = {
            "Node ID": [],
            "Queue Length": [],
            "Collisions": [],
            "Successful Tms": [],
            "Tms Attempts": []
        }
        
        for node in st.session_state.network_csma.nodes:
            stats_df["Node ID"].append(node.node_id)
            stats_df["Queue Length"].append(len(node.transmission_queue))
            stats_df["Collisions"].append(node.collision_count)
            stats_df["Successful Tms"].append(node.successful_transmissions)
            stats_df["Tms Attempts"].append(node.transmission_attempts)
        
        node_stats_placeholder.subheader("Node Statistics")
        node_stats_placeholder.dataframe(pd.DataFrame(stats_df))
        
        # Show history
        history_placeholder.text_area("Event Log", 
                                      "\n".join(st.session_state.network_csma.history[-10:]),
                                      height=200)
    
    # Autorun simulation button
    col1, col2 = st.columns(2)
    steps_to_run = col1.number_input("Number of steps to run", min_value=10, max_value=1000, value=100, step=10)
    
    if col2.button(f"Auto Run ({steps_to_run} steps)"):
        progress_bar = st.progress(0)
        
        for i in range(int(steps_to_run)):
            # Update network state
            st.session_state.network_csma.generate_random_traffic(traffic_rate)
            st.session_state.network_csma.update()
            st.session_state.step += 1
            
            # Update progress bar
            progress_bar.progress((i+1)/steps_to_run)
            
            # Slow down simulation for visualization
            time.sleep(0.1 / simulation_speed)
            
            # Update visualization periodically
            if i % 5 == 0 or i == steps_to_run-1:
                fig = st.session_state.network_csma.visualize()
                vis_placeholder.pyplot(fig)
                plt.close()
                
                # Update statistics displays
                collision_stats = st.session_state.network_csma.get_collision_statistics()
                collision_stats_placeholder.subheader("Network Statistics")
                collision_stats_placeholder.json(collision_stats)
                
                # Show node statistics
                stats_df = {
                    "Node ID": [],
                    "Queue Length": [],
                    "Collisions": [],
                    "Successful Tms": [],
                    "Tms Attempts": []
                }
                
                for node in st.session_state.network_csma.nodes:
                    stats_df["Node ID"].append(node.node_id)
                    stats_df["Queue Length"].append(len(node.transmission_queue))
                    stats_df["Collisions"].append(node.collision_count)
                    stats_df["Successful Tms"].append(node.successful_transmissions)
                    stats_df["Tms Attempts"].append(node.transmission_attempts)
                
                node_stats_placeholder.subheader("Node Statistics")
                node_stats_placeholder.dataframe(pd.DataFrame(stats_df))
        
        # Show final collision rate graph
        fig = plt.figure(figsize=(10, 4))
        times = [m["time"] for m in st.session_state.network_csma.metrics_history]
        collision_rates = [m["collision_rate"] for m in st.session_state.network_csma.metrics_history]
        
        plt.plot(times, collision_rates, 'r-', linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('Collision Rate')
        plt.title('Network Collision Rate Over Time')
        plt.grid(True)
        
        st.subheader("Final Collision Rate Analysis")
        st.pyplot(fig)
        plt.close()
        
        
        # Show history
        history_placeholder.text_area("Event Log", 
                                     "\n".join(st.session_state.network_csma.history[-20:]),
                                     height=200)

