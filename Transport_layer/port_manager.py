import random

class PortManager:
    def __init__(self):
        self.well_known_ports = {
            'http': 80,
            'ftp': 21,
            'ssh': 22,
            'smtp': 25,
            'dns': 53,
            'telnet': 23
            
        }
        self.ephemeral_start = 49152
        self.ephemeral_end = 65535
        self.assigned_ports = set()

    def assign_well_known_port(self, service_name):
        port = self.well_known_ports.get(service_name.lower())
        if port and port not in self.assigned_ports:
            self.assigned_ports.add(port)
            return port
        return None

    def assign_ephemeral_port(self):
        for _ in range(1000):
            port = random.randint(self.ephemeral_start, self.ephemeral_end)
            if port not in self.assigned_ports:
                self.assigned_ports.add(port)
                return port
        raise RuntimeError("No free ephemeral port available.")

    def release_port(self, port):
        if port in self.assigned_ports:
            self.assigned_ports.remove(port)
