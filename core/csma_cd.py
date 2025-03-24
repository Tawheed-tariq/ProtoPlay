import streamlit as st
import random
import time
from collections import deque

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.backoff_counter = 0
        self.max_backoff_attempts = 10
        self.transmission_queue = deque()
        self.current_packet = None
        self.state = "IDLE"  
        self.collision_count = 0
        self.successful_transmissions = 0
        self.color = "blue"
        self.transmission_start_time = 0
        self.transmission_attempts = 0

    def generate_packet(self, destination, size):
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
        return network.channel_state == "FREE"

    def start_transmission(self, network):
        if self.transmission_queue:
            self.current_packet = self.transmission_queue.popleft()
            self.state = "TRANSMITTING"
            network.channel_state = "BUSY"
            network.current_transmitters.append(self)
            self.color = "red"
            self.transmission_start_time = network.current_time
            self.transmission_attempts += 1
            network.history.append(f"Node {self.node_id} started transmitting packet {self.current_packet['id']} to Node {self.current_packet['destination']}")
            return True
        return False

    def handle_collision(self):
        self.collision_count += 1
        self.state = "BACKOFF"
        if self.collision_count > self.max_backoff_attempts:
            self.current_packet = None
            self.collision_count = 0
            self.state = "IDLE"
            self.color = "blue"
        else:
            max_backoff = 2 ** min(self.collision_count, 10)
            self.backoff_counter = random.randint(0, max_backoff - 1)
            self.color = "orange"

    def update(self, network):
        previous_state = self.state
        
        if self.state == "IDLE" and self.transmission_queue:
            self.state = "SENSING"
            self.color = "yellow"
            if previous_state != self.state:
                network.history.append(f"Node {self.node_id} changed state from {previous_state} to {self.state}")
        
        elif self.state == "SENSING":
            if self.sense_channel(network):
                self.start_transmission(network)
        
        elif self.state == "BACKOFF":
            self.backoff_counter -= 1
            network.history.append(f"Node {self.node_id} in BACKOFF state, counter: {self.backoff_counter}")
            
            if self.backoff_counter <= 0:
                self.state = "SENSING"
                self.color = "yellow"
                network.history.append(f"Node {self.node_id} changed state from BACKOFF to SENSING")
        
        elif self.state == "TRANSMITTING":
            if self.current_packet:
                packet_id = self.current_packet['id']
                dest = self.current_packet['destination']
                network.history.append(f"Node {self.node_id} continuing transmission of packet {packet_id} to Node {dest}, progress: {network.transmission_progress}/{network.transmission_duration}")
        
        return self.state


class Network:
    def __init__(self, num_nodes=5, collision_probability=0.1):
        self.nodes = [Node(i) for i in range(num_nodes)]
        self.channel_state = "FREE"
        self.current_transmitters = []
        self.transmission_progress = 0
        self.transmission_duration = 3  
        self.collision_detected = False
        self.collision_probability = collision_probability  
        self.history = []  
        self.current_time = 0
        self.collision_events = []  
        self.collision_count = 0
        self.successful_transmissions = 0
        self.collision_rate = 0
        self.metrics_history = []
        
    
    def update(self):
        self.current_time += 1
        self.history.append(f"--- Time step {self.current_time} ---")
        
        self.history.append(f"Channel state: {self.channel_state}")
        if self.current_transmitters:
            transmitter_ids = [node.node_id for node in self.current_transmitters]
            self.history.append(f"Current transmitters: {transmitter_ids}")
        
        for node in self.nodes:
            node.update(self)
        
        if (self.current_transmitters and len(self.current_transmitters) >= 1 and 
            random.random() < self.collision_probability):
            
            sensing_nodes = [node for node in self.nodes if node.state == "SENSING"]
            
            if sensing_nodes:
                force_node = random.choice(sensing_nodes)
                force_node.start_transmission(self)
                self.history.append(f"Node {force_node.node_id} started transmission while channel busy (forced collision)")
        
        if self.current_transmitters:
            if len(self.current_transmitters) > 1:
                self.handle_collision()
            else:
                self.transmission_progress += 1
                self.history.append(f"Transmission progress: {self.transmission_progress}/{self.transmission_duration}")
                
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
                    self.history.append(f"Channel state changed to FREE")
        
        total_attempts = self.collision_count + self.successful_transmissions
        self.collision_rate = self.collision_count / max(1, total_attempts)
        
        self.metrics_history.append({
            "time": self.current_time,
            "collisions": self.collision_count,
            "successful_transmissions": self.successful_transmissions,
            "collision_rate": self.collision_rate
        })
    
    def handle_collision(self):
        self.collision_count += 1
        involved_nodes = [node.node_id for node in self.current_transmitters]
        self.history.append(f"Collision detected between nodes {involved_nodes}")
        self.collision_detected = True
        
        self.collision_events.append({
            "time": self.current_time,
            "nodes": involved_nodes,
            "display_until": self.current_time + 5  # Display collision for 5 time steps
        })
        
        for node in self.current_transmitters:
            node.handle_collision()
            self.history.append(f"Node {node.node_id} enters BACKOFF state with counter {node.backoff_counter}")
        
        self.current_transmitters = []
        self.transmission_progress = 0
        self.channel_state = "FREE"
        self.collision_detected = False
        self.history.append(f"Channel state changed to FREE after collision")

    def generate_random_traffic(self, probability=0.1):
        for node in self.nodes:
            if node.state == "IDLE" and random.random() < probability:
                dest = random.choice([n for n in range(len(self.nodes)) if n != node.node_id])
                size = random.randint(1, 10)
                packet = node.generate_packet(dest, size)
                self.history.append(f"Node {node.node_id} generated packet {packet['id']} for Node {dest}")

    def get_collision_statistics(self):
        """Get collision statistics for display"""
        stats = {
            "Total Collisions": self.collision_count,
            "Successful Transmissions": self.successful_transmissions,
            "Current Collision Rate": f"{self.collision_rate:.2f}",
            "Channel State": self.channel_state
        }
        return stats
