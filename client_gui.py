import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextBrowser, QLabel, QGroupBox,
)
from PySide6.QtCore import Slot
import qdarktheme

from client_network import ChatNetworkWorker

class ChatClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp-like LAN Chat")
        self.resize(550, 750)

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

        conn_group = QGroupBox("Server & User Details")
        conn_layout = QHBoxLayout(conn_group)

        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setPlaceholderText("Host IP")
        
        self.port_input = QLineEdit("8888")
        self.port_input.setPlaceholderText("Port")
        self.port_input.setFixedWidth(60)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Your Name")
        self.user_input.setText("Bob")
        self.user_input.setFixedWidth(80)

        self.conn_btn = QPushButton("Connect")
        self.conn_btn.setFixedWidth(90)

        conn_layout.addWidget(QLabel("Host:"))
        conn_layout.addWidget(self.host_input, 1)
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_input)
        conn_layout.addWidget(QLabel("You:"))
        conn_layout.addWidget(self.user_input)
        conn_layout.addWidget(self.conn_btn)

        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: #888; font-weight: bold;")

        # Target Contact Group
        target_group = QWidget()
        target_layout = QHBoxLayout(target_group)
        target_layout.setContentsMargins(0, 0, 0, 0)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target Username (Leave empty or 'All' to broadcast)")
        target_layout.addWidget(QLabel("<b>Contact:</b>"))
        target_layout.addWidget(self.target_input, 1)

        # Chat Area (HTML supported)
        self.chat_log = QTextBrowser()
        self.chat_log.setReadOnly(True)
        self.chat_log.setOpenExternalLinks(True)
        self.chat_log.setStyleSheet("background-color: #0b141a; border-radius: 8px;")
        
        # Bottom Input Area
        input_bar = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self._send_message)
        self.msg_input.setFixedHeight(40)
        self.msg_input.setStyleSheet("border-radius: 20px; padding-left: 15px; background-color: #2a3942; color: white;")

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(40)
        self.send_btn.setFixedWidth(70)
        self.send_btn.setStyleSheet("border-radius: 20px; background-color: #00a884; color: white; font-weight: bold;")

        input_bar.addWidget(self.msg_input, 1)
        input_bar.addWidget(self.send_btn)

        layout.addWidget(conn_group)
        layout.addWidget(target_group)
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
                return
            try:
                port = int(self.port_input.text().strip())
            except ValueError:
                return
            username = self.user_input.text().strip() or "Guest"
            self.network_worker.connect_to_server(host, port, username)
        else:
            self.network_worker.disconnect()

    def _append_html_bubble(self, sender: str, text: str, is_me: bool):
        # We use a table to float the bubble left or right properly inside QTextBrowser
        if is_me:
            html = f"""
            <table width="100%"><tr>
                <td width="20%"></td>
                <td style="background-color: #005c4b; border-radius: 10px; padding: 10px; color: #e9edef;">
                    <div style="font-size: 11px; color: #1dda95; margin-bottom: 3px;"><b>You</b></div>
                    <div style="font-size: 14px;">{text}</div>
                </td>
            </tr></table><br>
            """
        else:
            html = f"""
            <table width="100%"><tr>
                <td style="background-color: #202c33; border-radius: 10px; padding: 10px; color: #e9edef;">
                    <div style="font-size: 11px; color: #53bdeb; margin-bottom: 3px;"><b>{sender}</b></div>
                    <div style="font-size: 14px;">{text}</div>
                </td>
                <td width="20%"></td>
            </tr></table><br>
            """
        self.chat_log.append(html)

    @Slot(str, str)
    def _display_message(self, sender: str, text: str):
        self._append_html_bubble(sender, text, is_me=False)

    @Slot(str)
    def _update_connection_state(self, state: str):
        if state == "CONNECTED":
            self.conn_btn.setText("Disconnect")
            self.conn_btn.setStyleSheet("color: white; background-color: #c62828; border: 1px solid #8e0000;")
            self.host_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.user_input.setEnabled(False)
            self.msg_input.setFocus()
            self.status_label.setText("Status: <span style='color:#00a884;'>Connected</span>")
        else:
            self.conn_btn.setText("Connect")
            self.conn_btn.setStyleSheet("")
            self.host_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.user_input.setEnabled(True)
            self.status_label.setText(f"Status: {state}")

    @Slot()
    def _send_message(self):
        text = self.msg_input.text().strip()
        target = self.target_input.text().strip() or "All"
        if text:
            # We display our own message immediately
            self._append_html_bubble("You", text, is_me=True)
            self.network_worker.send_text(target, text)
            self.msg_input.clear()

    def closeEvent(self, event):
        self.network_worker.quit()
        if self.network_worker.isRunning():
            self.network_worker.wait(1500)
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet(theme="dark"))
    window = ChatClientGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
