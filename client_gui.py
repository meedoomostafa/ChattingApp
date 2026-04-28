import socket
from typing import Dict, Tuple
import threading

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