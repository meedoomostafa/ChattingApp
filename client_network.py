import socket
import struct
import queue
import threading
from PySide6.QtCore import QThread, Signal, Slot

class ChatNetworkWorker(QThread):
    message_received = Signal(str, str)
    connection_state_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.sock: socket.socket | None = None
        self.username: str = ""
        self.msg_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._host: str | None = None
        self._port: int | None = None

    @Slot(str, int, str)
    def connect_to_server(self, host: str, port: int, username: str):
        self._host = host
        self._port = port
        self.username = username
        if not self.isRunning():
            self._stop_event.clear()
            self.start()

    @Slot(str, str)
    def send_text(self, target: str, text: str):
        payload = f"{self.username}::{target}::{text}"
        self.msg_queue.put(payload)

    @Slot()
    def disconnect(self):
        self._stop_event.set()
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.wait(2000)

    def run(self):
        if not self._host or not self._port:
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self._host, self._port))
            self.connection_state_changed.emit("CONNECTED")
        except Exception as e:
            self.connection_state_changed.emit(f"Error: {str(e)}")
            return

        self._stop_event.clear()

        while not self._stop_event.is_set():
            try:
                # Timeout allows periodic evaluation of _stop_event without select/poll
                self.sock.settimeout(1.0)
                
                header = self._recv_exact(4)
                if not header:
                    break

                payload_len = struct.unpack("!I", header)[0]
                raw_payload = self._recv_exact(payload_len)
                if raw_payload:
                    payload_str = raw_payload.decode("utf-8")
                    if payload_str.count("::") >= 2:
                        sender, target, text = payload_str.split("::", 2)
                        # Filter for target
                        if target == self.username or target == "All" or not target:
                            self.message_received.emit(sender, text)
                    elif "::" in payload_str:
                        sender, text = payload_str.split("::", 1)
                        self.message_received.emit(sender, text)

            except socket.timeout:
                pass
            except (ConnectionResetError, BrokenPipeError, OSError):
                break
            except Exception as e:
                self.connection_state_changed.emit(f"Error: {str(e)}")
                break

            # Drain outgoing queue without blocking the receive loop
            while not self.msg_queue.empty():
                try:
                    msg = self.msg_queue.get_nowait()
                    self._send_payload(msg.encode("utf-8"))
                except queue.Empty:
                    break

        self._cleanup()

    def _recv_exact(self, n: int) -> bytes:
        buffer = bytearray()
        while len(buffer) < n:
            try:
                chunk = self.sock.recv(n - len(buffer))
                if not chunk:
                    return bytes(buffer)
                buffer.extend(chunk)
            except (ConnectionResetError, BrokenPipeError):
                return bytes(buffer)
        return bytes(buffer)

    def _send_payload(self, data: bytes):
        try:
            header = struct.pack("!I", len(data))
            self.sock.sendall(header + data)
        except OSError:
            self.disconnect()

    def _cleanup(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        self.connection_state_changed.emit("DISCONNECTED")