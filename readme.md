# Flask Socket Server and Client

## Description
This project consists of a server and a client implementation. The server uses Flask and Python's `socket` and `threading` libraries to manage connections, handle file transfers, and execute commands on connected agents. The client connects to the server, receives commands, executes them, and handles file transfers. The project also includes a web interface for managing agents.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
- [Endpoints](#endpoints)
- [Client Functionality](#client-functionality)
- [Web Interface](#web-interface)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact Information](#contact-information)

## Installation

### Prerequisites
- Python 3.6+
- Flask

### Step-by-Step Guide
1. Clone the repository:
   ```bash
   git clone https://github.com/Surajkumarsaw1/CypherC2.git
   cd CypherC2
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create the uploads directory if it doesn't exist:
   ```bash
   mkdir -p uploads
   ```

4. Run the server:
   ```bash
   python server.py
   ```

5. Run the client (in a separate terminal):
   ```bash
   python client.py
   ```

## Usage

### Starting the Server
Run the following command to start the server:
```bash
python server.py
```

### Connecting Agents
Agents can connect to the server at `127.0.0.1:1234`.

### Sending Commands to Agents
Commands can be sent to agents via the Flask web interface. Navigate to `http://127.0.0.1:5000` to interact with the agents.

### Running the Client
Run the following command to start the client:
```bash
python client.py
```

## Features
- Handles multiple agent connections using threads.
- Allows sending and receiving commands to/from agents.
- Supports file transfers with chunk verification and hash validation.
- Provides a web interface to manage agents and execute commands.

## Configuration
The server and client configuration parameters can be adjusted in their respective files:

### Server Configuration (`server.py`)
- `ip_address`: The IP address of the server (default is `'127.0.0.1'`).
- `port_number`: The port number for the socket server (default is `1234`).
- `UPLOAD_FOLDER`: Directory for storing uploaded files (default is `'uploads'`).
- `RECV_SIZE`: Size of data chunks to receive from agents (default is `1MB`).
- `CHUNK_SIZE`: Size of file chunks to send to agents (default is `1024 * 1020`).

### Client Configuration (`client.py`)
- `ip`: The IP address of the server (default is `'127.0.0.1'`).
- `port`: The port number for the socket server (default is `1234`).
- `RECV_SIZE`: Size of data chunks to receive from the server (default is `1MB`).
- `CHUNK_SIZE`: Size of file chunks to send to the server (default is `1024 * 1020`).

## Endpoints

### `/`
- **Method:** GET
- **Description:** Home page of the web interface.

### `/agents`
- **Method:** GET
- **Description:** Lists all connected agents with their details.

### `/<agentname>/terminal`
- **Method:** GET
- **Description:** Terminal interface for sending commands to the specified agent.

### `/<agentname>/execute`
- **Method:** POST
- **Description:** Executes a command on the specified agent.
- **Request Body:**
  ```json
  {
    "command": "your-command"
  }
  ```
- **Response:**
  ```json
  {
    "output": "command-output"
  }
  ```

## Client Functionality

### Connecting to the Server
The client connects to the server at the specified IP and port.

### Receiving Commands
The client waits to receive commands from the server. Commands are expected in a dictionary format.

### Executing Commands
The client can execute shell commands or handle file transfers based on the received command type.

### File Transfer
- The client handles file chunks, verifies their hashes, and reassembles them.
- The client can also send file chunks to the server upon request.

### Command Handling
- If the command is to transfer a file, the client reads the file in chunks and sends them to the server.
- If the command is a shell command, the client executes it and sends the output back to the server.

## Web Interface

### `index.html`
This is the home page of the web interface.

### `agents.html`
This page lists all connected agents with their details.

### `terminal.html`
This page provides a terminal interface for sending commands to the specified agent.

## Error Handling
- **Connection Errors:** The server and client handle connection errors using try-except blocks to catch `ConnectionError` exceptions. When a connection error occurs, a message is printed, and the connection is closed gracefully.
- **Invalid Commands:** If the client receives an invalid command format, it catches `SyntaxError` and `ValueError` exceptions, logs an error message, and continues to wait for valid commands.
- **File Handling Errors:** Errors that occur during file operations (e.g., reading or writing files) are caught and logged. The client sends an appropriate error message back to the server.

## Security Considerations
- **Input Validation:** The client uses `ast.literal_eval` to safely parse commands from the server, ensuring that only valid Python literals are processed.
- **File Handling:** When transferring files, the client and server verify the integrity of file chunks using SHA-256 hashes. This helps prevent data corruption and ensures that the transferred files are intact.
- **Command Execution:** The client executes shell commands with caution, capturing both standard output and standard error to prevent unexpected behavior.

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Make your changes.
4. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
5. Push to the branch:
   ```bash
   git push origin feature-branch
   ```
6. Create a pull request.

## License
This project is licensed under the Limited MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
- Thanks to the contributors of Flask and Python for their wonderful libraries.

## Contact Information
For any questions or support, please contact [Contact Me](https://dsa.pythonanywhere.com/contact).