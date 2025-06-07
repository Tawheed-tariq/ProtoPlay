import socket

def start_client(server_port, client_port, log):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', client_port))
        s.connect(('localhost', server_port))
        log.append(f"[Client] Connected to server on port {server_port} from port {client_port}")
        s.sendall(f"Hello from client on port {client_port}".encode())
        reply = s.recv(1024).decode()
        log.append(f"[Client] Received: {reply}")
