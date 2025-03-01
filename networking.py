import os
import socket
from datetime import datetime
import vpn_networking

LISTENING_PORT = 5001
BUFFER_SIZE = 4096

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
            # Receive file name
            file_name_data = conn.recv(self.BUFFER_SIZE)
            try:
                file_name = file_name_data.decode("utf-8").strip()
                # Ensure the file name is valid and has an extension
                if not os.path.splitext(file_name)[1]:
                    file_name = "received_file"
            except UnicodeDecodeError:
                print("[-] Invalid file name received (not UTF-8). Using default name.")
                file_name = "received_file"

            print(f"[+] Receiving file: {file_name}")

            # Determine file type
            file_type = os.path.splitext(file_name)[1].lower()

            # Initialize save_path
            save_path = ""

            if file_type == ".json":
                save_path = f"/tmp/{file_name}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                save_path = os.path.join(self.SAVE_PATH, f"{timestamp}_{file_name}")

            # Save the file
            with open(save_path, "wb") as file:
                total_received = 0
                while True:
                    data = conn.recv(self.BUFFER_SIZE)
                    if not data:
                        break
                    file.write(data)
                    total_received += len(data)
                    print(f"[+] Received {total_received} bytes so far...")

            print(f"[+] File received successfully: {save_path}")
            print(f"[+] Total bytes received: {total_received}")
        except Exception as e:
            print(f"[-] Error receiving file: {e}")
        finally:
            # Ensure the connection is always closed
            conn.close()
            print("[+] Connection closed.")

    def send_file(self, file_path, dest_ip):
        """Send a file to the specified destination IP."""
        if not os.path.isfile(file_path):
            print(f"[-] File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        print(f"[*] Connecting to server at {dest_ip}:{self.LISTEN_PORT}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((dest_ip, self.LISTEN_PORT))
                print("[+] Connected to server")

                client_socket.send(file_name.encode("utf-8"))
                with open(file_path, "rb") as file:
                    while chunk := file.read(self.BUFFER_SIZE):
                        client_socket.send(chunk)

                print(f"[+] File {file_name} sent successfully!")
        except Exception as e:
            print(f"[-] Error sending file: {e}")