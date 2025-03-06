import streamlit as st

class Switch:
    def __init__(self, switch_id):
        self.id = switch_id
        self.connected_devices = []  # Stores connected devices/hubs
        self.mac_table = {}  # MAC: port
        self.max_ports = 2  # 2-port switch

    def is_port_available(self):
        return len(self.connected_devices) < self.max_ports

    def transmit(self, source, data, destination):
        if destination.mac in self.mac_table:
            # Forward to the specific port
            self.mac_table[destination.mac].receive(data)
        else:
            # Flood to all ports except source
            for device in self.connected_devices:
                if device != source:
                    device.receive(data)
            # Learn the MAC address
            self.mac_table[source.mac] = source

class Frame:
    def __init__(self, src_mac, dest_mac, data):
        self.src_mac = src_mac
        self.dest_mac = dest_mac
        self.data = data
        self.crc = self.calculate_crc()

    def calculate_crc(self):
        # Simplified CRC example (use binascii.crc32 in real code)
        return sum(bytes(self.data, 'utf-8')) % 256