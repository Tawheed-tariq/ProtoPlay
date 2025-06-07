import socket

def start_server(port, log):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', port))
        s.listen()
        log.append(f"[Server] Listening on port {port}")
        conn, addr = s.accept()
        with conn:
            log.append(f"[Server] Connected by {addr}")
            msg = conn.recv(1024).decode()
            log.append(f"[Server] Received: {msg}")
            reply = f"Reply from server at port {port}"
            conn.sendall(reply.encode())
            log.append(f"[Server] Sent: {reply}")
