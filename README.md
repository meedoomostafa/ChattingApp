# Local Chat Application

A simple, local-network chat application written in Python using PySide6 (Qt) for the graphical interface and standard sockets for networking. The application functions similarly to a group chat with a server-client architecture.

## Features
- **Server:** Handles multiple client connections concurrently and broadcasts messages across the network.
- **Client (GUI):** A WhatsApp-style dark-mode interface allowing users to connect to the server, send messages to all users, or message a specific user individually.
- **Networking:** Utilizes reliable TCP sockets with a custom framing mechanism to ensure messages are received intact.

## Prerequisites
Ensure you have Python installed on your system along with the necessary library dependencies.

Install dependencies using pip:
pip install -r requirements.txt

## How to use

1. **Start the Server:**
   Run the server script and follow the prompts to specify the bind address (usually `127.0.0.1` for local setup) and the port.
   python server.py

2. **Start the Client:**
   Launch the user interface to connect to the server.
   python client_gui.py

   - Fill out your connection details in the top section (Host, Port, Your Name).
   - Enter a target username to send a direct message, or leave it empty/use 'All' to broadcast to everyone.
   - Click "Connect" and start typing messages in the bottom input bar.
