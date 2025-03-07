from core.data_link import Switch, Frame
import streamlit as st

class EndDevice:
    def __init__(self, device_id, mac_address):
        self.id = device_id
        self.mac = mac_address
        self.connected_to = None  # Hub, Switch, or direct connection

    def send(self, data, destination, layer="physical"):
        if layer == "data_link":
            # Create a frame for Data Link Layer
            frame = Frame(self.mac, destination.mac, data)
            if self.connected_to:
                self.connected_to.transmit(self, frame, destination)
            else:
                # Direct connection (device-to-device)
                destination.receive(data)
        else:
            st.write(f"Device {self.id} sending data to {destination.id}")
            st.write(f"{self.id} is connected to {self.connected_to.id}")
            if self.connected_to == destination:
                # Direct connection (device-to-device)
                st.write(f"Device {self.id} sending data directly to {destination.id}")
                destination.receive(data)
                return True
            else:
                # Log transmission in Streamlit UI
                st.write(f"Device {self.id} sending data to {destination.id} via {self.connected_to.id}")
                success = self.connected_to.transmit(self, data, destination)
                return True
                
    def transmit(self, source, data, destination):
        if self.connected_to != destination:
            self.connected_to.transmit(self, data, destination)
        else:
            # Direct connection (device-to-device)
            destination.receive(data)
        

    def receive(self, data):
        st.success(f"Device {self.id} received data: {data}")

class Hub:
    def __init__(self, hub_id):
        self.id = hub_id
        self.connected_devices = []

    def transmit(self, source, data, destination):
        # Check if destination is directly connected to the hub
        data_reached = (destination in self.connected_devices) and (destination != source)

        # Log connected devices in Streamlit UI
        st.write(f"Hub {self.id} Connected Devices: {[d.id for d in self.connected_devices]}")

        # Broadcast data to all connected devices except the source
        for device in self.connected_devices:
            if device != source:
                device.receive(data)
                st.write(f"Hub {self.id} sent data to {device.id}")

        return data_reached  # Return True if data reached the destination

class Network:
    def __init__(self):
        self.devices = []  # List of end devices
        self.hubs = []     # List of hubs
        self.switches = [] # List of switches (for Data Link Layer)
        self.connections = []  # List of connections between entities

    def add_device(self, device):
        self.devices.append(device)

    def add_hub(self, hub):
        self.hubs.append(hub)

    def add_switch(self, switch):
        self.switches.append(switch)

    def connect(self, entity1, entity2):
        # Check if either entity is a switch with no available ports
        st.write(f"entity1 : {isinstance(entity1, Hub)}, entity2 : {isinstance(entity2, EndDevice)}")
        if isinstance(entity1, Switch) and not entity1.is_port_available():
            return False, f"Switch {entity1.id} has no available ports (max 2)."
        if isinstance(entity2, Switch) and not entity2.is_port_available():
            return False, f"Switch {entity2.id} has no available ports (max 2)."

        # Logic for hubs
        if isinstance(entity1, Hub) and isinstance(entity2, EndDevice):
            entity1.connected_devices.append(entity2)  # Add device to hub's connected_devices
            entity2.connected_to = entity1
            st.write(f"Debug: Added {entity2.id} to {entity1.id}'s connected_devices")
        elif isinstance(entity2, Hub) and isinstance(entity1, EndDevice):
            entity2.connected_devices.append(entity1)  # Add device to hub's connected_devices
            entity1.connected_to = entity2
            st.write(f"Debug: Added {entity1.id} to {entity2.id}'s connected_devices")

        # Logic for switches
        elif isinstance(entity1, Switch):
            entity1.connected_devices.append(entity2)
            entity2.connected_to = entity1
        elif isinstance(entity2, Switch):
            entity2.connected_devices.append(entity1)
            entity1.connected_to = entity2

        # Direct connection (e.g., device-to-device)
        else:
            entity1.connected_to = entity2
            entity2.connected_to = entity1

        self.connections.append((entity1, entity2))
        return True, f"Connected {entity1.id} and {entity2.id}."