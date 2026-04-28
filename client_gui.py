import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
import qdarktheme

from client_network import ChatNetworkWorker


class ChatClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LAN Chat Client")
        self.resize(520, 680)

        self.network_worker = ChatNetworkWorker()
        self.network_worker.message_received.connect(self._display_message)
        self.network_worker.connection_state_changed.connect(self._update_connection_state)

        self._build_ui()
        self.network_worker.start()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        conn_group = QGroupBox("Server Connection")
        conn_layout = QHBoxLayout(conn_group)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host IP")
        self.host_input.setText("127.0.0.1")

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port")
        self.port_input.setText("8888")
        self.port_input.setFixedWidth(70)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setText("Guest")
        self.user_input.setFixedWidth(90)

        self.conn_btn = QPushButton("Connect")
        self.conn_btn.setFixedWidth(100)

        conn_layout.addWidget(QLabel("Host:"))
        conn_layout.addWidget(self.host_input, 1)
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_input)
        conn_layout.addWidget(QLabel("Name:"))
        conn_layout.addWidget(self.user_input)
        conn_layout.addWidget(self.conn_btn)

        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: #888; padding-left: 4px;")

        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setPlaceholderText("Chat messages will appear here...")
        self.chat_log.setFont(QFont("Consolas", 10))

        input_bar = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type message and press Enter...")
        self.msg_input.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)

        input_bar.addWidget(self.msg_input, 1)
        input_bar.addWidget(self.send_btn)

        layout.addWidget(conn_group)
        layout.addWidget(self.status_label)
        layout.addWidget(self.chat_log, 1)
        layout.addLayout(input_bar)

        self.conn_btn.clicked.connect(self._toggle_connection)
        self.send_btn.clicked.connect(self._send_message)

    @Slot()
    def _toggle_connection(self):
        if self.conn_btn.text() == "Connect":
            host = self.host_input.text().strip()
            if not host:
                self.status_label.setText("Status: Host address required")
                return

            try:
                port = int(self.port_input.text().strip())
            except ValueError:
                self.status_label.setText("Status: Invalid port number")
                return

            username = self.user_input.text().strip() or "Anonymous"
            self.network_worker.connect_to_server(host, port, username)
        else:
            self.network_worker.disconnect()

    @Slot(str, str)
    def _display_message(self, sender: str, text: str):
        self.chat_log.append(f"[{sender}] {text}")

    @Slot(str)
    def _update_connection_state(self, state: str):
        if state == "CONNECTED":
            self.conn_btn.setText("Disconnect")
            self.conn_btn.setStyleSheet("color: white; background-color: #c62828; border: 1px solid #8e0000;")
            self.host_input.setReadOnly(True)
            self.port_input.setReadOnly(True)
            self.user_input.setReadOnly(True)
            self.msg_input.setFocus()
        else:
            self.conn_btn.setText("Connect")
            self.conn_btn.setStyleSheet("")
            self.host_input.setReadOnly(False)
            self.port_input.setReadOnly(False)
            self.user_input.setReadOnly(False)

        self.status_label.setText(f"Status: {state}")

    @Slot()
    def _send_message(self):
        text = self.msg_input.text().strip()
        if text:
            self.network_worker.send_text(text)
            self.msg_input.clear()

    def closeEvent(self, event):
        self.network_worker.quit()
        if self.network_worker.isRunning():
            self.network_worker.wait(1500)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet())
    window = ChatClientGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()