import socket
from typing import Dict, Tuple
import threading
import sys
import struct

class ChatServer:
    def __init__(self, host:str, port:int):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Here we map the socket with (ip:str, port:int)
        self.clients: Dict[socket.socket, Tuple[str, int]] = {}
        # Intuitively, it prevents Raceconditions
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.accept_thread: threading.Thread | None = None

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(socket.SOMAXCONN)
        print(f"listing on {self.host}:{self.port}")

        self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        self.accept_thread.start()

        try:
            while self.accept_thread.is_alive():
                self.accept_thread.join(timeout=1)
        except KeyboardInterrupt:
            self.stop()
            sys.exit(0)

    def _accept_connections(self):
        self.server_socket.settimeout(1.0)
        while not self.stop_event.is_set():
            try:
                client_sock, addr = self.server_socket.accept()
                print(f"[server] new connection {addr[0]}:{addr[1]}")
                handler = threading.Thread(target=self._handle_client, args=(client_sock, addr))
                handler.start()
            except socket.timeout:
                continue
            except OSError:
                if not self.stop_event.is_set():
                    print(f"[server] accept loop interrupted.")
                break
    
    def _handle_client(self, client_sock: socket.socket, addr: Tuple[str, int]):
        with self.lock():
            self.clients[client_sock] = addr

        try:
            while not self.stop_event.is_set():
                payload = self._receive_framed(client_sock)
                if not payload:
                    break
                self._broadcast(payload, client_sock)
        except(ConnectionResetError, BrokenPipeError):
            pass
        finally:
            self._cleanup_client(client_sock)
    
    def _receive_framed(self, sock: socket.socket):
        header = self._receive_exact(sock, 4)
        if not header:
            return b""
        payload_len = struct.unpack("!I", header)[0]
        return self._receive_exact(sock, payload_len)
    
    def _receive_exact(self, sock: socket.socket, n: int):
        buffer = bytearray()
        while len(buffer) < n:
            chunk = sock.recv(n - len(buffer))
            if not chunk:
                return bytes(buffer)
            buffer.extend(chunk)
        return bytes(buffer)
    
    def _broadcast(self, payload: bytes, sender_sock: socket.socket):
        with self.lock:
            snapshot = dict(self.clients)
        
        for client_sock in snapshot:
            if client_sock is not sender_sock:
                self._send_framed(client_sock, payload)
    
    def _send_framed(self, sock: socket.socket, payload: bytes):
        header = struct.pack("!I", len(payload))
        try:
            sock.sendall(header + payload)
        except(ConnectionResetError, BrokenPipeError, OSError):
            self._cleanup_client(sock)

    def _cleanup_client(self, sock: socket.socket):
        with self.lock:
            addr = self.clients.pop(sock, None)
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        if addr:
            print(f"[server] client left {addr[0]}:{addr[1]}")
    
    def stop(self):
        print("\n[Server] Shutting down...")
        self.stop_event.set()
        try:
            self.server_socket.close()
        except OSError:
            pass

        with self.lock:
            active_sockets = list(self.clients.keys())
        for s in active_sockets:
            self._cleanup_client(s)

        if self.accept_thread:
            self.accept_thread.join(timeout=2.0)
        print("[server] Stopped.")

def main():
    default_host = "127.0.0.1"
    default_port = "8888"
    host = input(f"Bind address (default: {default_host}): ").strip() or default_host
    port = int(input(f"Port (default: {default_port}): ").strip() or default_port)
    ChatServer(host, port).start()

if __name__ == "__main__":
    main()