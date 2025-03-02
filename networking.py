import os
import socket
import sys
from datetime import datetime

LISTENING_PORT = 5001
BUFFER_SIZE = 8192  # Smaller buffer size to reduce packet loss

class Networking:
    """Handles file transfer over the network."""

    def __init__(self):
        self.LISTEN_PORT = LISTENING_PORT
        self.HOST_IP = self.extract_address()  # Bind to all available interfaces
        self.BUFFER_SIZE = BUFFER_SIZE
        self.SAVE_PATH = "received_files"  # Directory to save received files
        self.server_socket = None
        self.is_running = False

    def extract_address(self, file_path="/etc/wireguard/wg0.conf"):
        """
        Extracts the 'Address' value from a WireGuard configuration file.

        Args:
            file_path (str): Path to the WireGuard configuration file.

        Returns:
            str: The extracted IP address.
        """
        try:
            with open(file_path, "r") as file:
                for line in file:
                    # Strip whitespace and check if the line starts with 'Address'
                    if line.strip().startswith("Address"):
                        # Extract the value after the '=' sign
                        address = line.split("=")[1].strip()
                        # Remove the subnet mask (e.g., '/24') if present
                        return address.split("/")[0]
        except FileNotFoundError:
            print(f"[-] File not found: {file_path}")
        except Exception as e:
            print(f"[-] Error reading file: {e}")

        return None

    def start_server(self):
        """Start the file transfer server."""
        print("[*] Starting server...")
        try:
            os.makedirs(self.SAVE_PATH, exist_ok=True)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.HOST_IP, self.LISTEN_PORT))
            self.server_socket.listen(5)
            self.is_running = True
            print(f"[*] Server listening on {self.HOST_IP}:{self.LISTEN_PORT}")

            while self.is_running:
                try:
                    conn, addr = self.server_socket.accept()
                    print(f"[+] Connection established with {addr}")
                    self.handle_client(conn)
                except socket.error as e:
                    if self.is_running:
                        print(f"[-] Server error: {e}")
        except Exception as e:
            print(f"[-] Failed to start server: {e}")
        finally:
            self.stop_server()

    def handle_client(self, conn):
        """Handle incoming client connections."""
        try:
            while True:
                # Receive file name
                file_name_data = conn.recv(self.BUFFER_SIZE)
                if not file_name_data:
                    break  # Connection closed by client

                try:
                    file_name = file_name_data.decode("utf-8").strip()
                except UnicodeDecodeError:
                    print("[-] Invalid file name received (not UTF-8). Using default name.")
                    file_name = "received_file"

                print(f"[+] Receiving file: {file_name}")

                # Initialize save_path
                save_path = os.path.join(self.SAVE_PATH, file_name)

                # Save the file
                received_bytes = 0
                with open(save_path, "wb") as file:
                    while True:
                        data = conn.recv(self.BUFFER_SIZE)
                        if not data:
                            break  # Connection closed by client

                        # Check for end-of-file marker
                        if data.endswith(b"<EOF>"):
                            file.write(data[:-5])  # Write data without the marker
                            received_bytes += len(data) - 5
                            break
                        file.write(data)
                        received_bytes += len(data)
                        print(f"[+] Received chunk size: {len(data)} bytes")

                print(f"[+] File received successfully: {save_path}")
                print(f"[+] Received file size: {received_bytes} bytes")

                # Send acknowledgment to the sender
                conn.send(b"ACK")
        except Exception as e:
            print(f"[-] Error receiving file: {e}")
        finally:
            # Ensure the connection is always closed
            conn.close()
            print("[+] Connection closed.")

    def stop_server(self):
        """Stop the file transfer server."""
        print("[*] Stopping server...")
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        print("[*] Server stopped.")

    def send_file(self, file_paths, dest_ip):
        """
        Send multiple files to the specified destination IP.

        Args:
            file_paths (list): List of file paths to send.
            dest_ip (str): Destination IP address.
        """
        if not all(os.path.isfile(file_path) for file_path in file_paths):
            print("[-] One or more files not found.")
            return

        print(f"[*] Connecting to server at {dest_ip}:{self.LISTEN_PORT}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((dest_ip, self.LISTEN_PORT))
                print("[+] Connected to server")

                for file_path in file_paths:
                    file_name = os.path.basename(file_path)
                    print(f"[*] Sending file: {file_name}")

                    # Send file name
                    client_socket.send(file_name.encode("utf-8"))

                    # Send file data
                    total_sent = 0
                    with open(file_path, "rb") as file:
                        while chunk := file.read(self.BUFFER_SIZE):
                            client_socket.send(chunk)
                            total_sent += len(chunk)
                            print(f"[+] Sent chunk size: {len(chunk)} bytes")

                    # Send end-of-file marker
                    client_socket.send(b"<EOF>")
                    print(f"[+] File {file_name} sent successfully!")
                    print(f"[+] Total bytes sent: {total_sent} bytes")

                    # Wait for acknowledgment from the receiver
                    ack = client_socket.recv(3)
                    if ack != b"ACK":
                        print(f"[-] Acknowledgment not received for {file_name}.")
                        return

                print("[+] All files sent successfully!")
        except Exception as e:
            print(f"[-] Error sending files: {e}")


