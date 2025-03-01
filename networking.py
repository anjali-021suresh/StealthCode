import os
import socket
from datetime import datetime
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
                    if line.strip().startswith("Address"):
                        address = line.split("=")[1].strip()
                        return address.split("/")[0]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error reading file: {e}")
        return None

    def start_server(self):
        """Start the file transfer server."""
        logger.info("Starting server...")
        try:
            os.makedirs(self.SAVE_PATH, exist_ok=True)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                self.server_socket = server_socket
                server_socket.bind((self.HOST_IP, self.LISTEN_PORT))
                server_socket.listen(5)
                self.is_running = True
                logger.info(f"Server listening on {self.HOST_IP}:{self.LISTEN_PORT}")

                while self.is_running:
                    try:
                        conn, addr = server_socket.accept()
                        logger.info(f"Connection established with {addr}")
                        self.handle_client(conn)
                    except socket.error as e:
                        if self.is_running:
                            logger.error(f"Server error: {e}")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.stop_server()

    def handle_client(self, conn):
        """Handle incoming client connections."""
        try:
            # Receive file name
            file_name = self.receive_file_name(conn)
            if not file_name:
                file_name = "received_file"

            logger.info(f"Receiving file: {file_name}")

            # Determine save path
            save_path = self.get_save_path(file_name)

            # Receive and save the file
            total_received = self.receive_file_data(conn, save_path)
            logger.info(f"File received successfully: {save_path}")
            logger.info(f"Total bytes received: {total_received}")

            # Verify file integrity (optional)
            if self.verify_file_integrity(save_path, total_received):
                logger.info("File integrity verified.")
            else:
                logger.warning("File integrity check failed.")
        except Exception as e:
            logger.error(f"Error receiving file: {e}")
        finally:
            conn.close()
            logger.info("Connection closed.")

    def receive_file_name(self, conn):
        """Receive and decode the file name from the client."""
        try:
            file_name_data = conn.recv(self.BUFFER_SIZE)
            file_name = file_name_data.decode("utf-8").strip()
            if not os.path.splitext(file_name)[1]:
                logger.warning("Invalid file name (no extension). Using default name.")
                return "received_file"
            return file_name
        except UnicodeDecodeError:
            logger.warning("Invalid file name received (not UTF-8). Using default name.")
            return "received_file"

    def get_save_path(self, file_name):
        """Generate the save path for the received file."""
        file_type = os.path.splitext(file_name)[1].lower()
        if file_type == ".json":
            return f"/tmp/{file_name}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return os.path.join(self.SAVE_PATH, f"{timestamp}_{file_name}")

    def receive_file_data(self, conn, save_path):
        """Receive file data and save it to the specified path."""
        total_received = 0
        with open(save_path, "wb") as file:
            while True:
                data = conn.recv(self.BUFFER_SIZE)
                if not data:
                    break
                file.write(data)
                total_received += len(data)
                logger.info(f"Received {total_received} bytes so far...")
        return total_received

    def verify_file_integrity(self, file_path, expected_size):
        """Verify the integrity of the received file."""
        if os.path.getsize(file_path) == expected_size:
            return True
        return False

    def stop_server(self):
        """Stop the file transfer server."""
        logger.info("Stopping server...")
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        logger.info("Server stopped.")

    def send_file(self, file_path, dest_ip):
        """Send a file to the specified destination IP."""
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        logger.info(f"Connecting to server at {dest_ip}:{self.LISTEN_PORT}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((dest_ip, self.LISTEN_PORT))
                logger.info("Connected to server")

                # Send file name
                client_socket.send(file_name.encode("utf-8"))

                # Send file data
                total_sent = 0
                with open(file_path, "rb") as file:
                    while chunk := file.read(self.BUFFER_SIZE):
                        client_socket.send(chunk)
                        total_sent += len(chunk)
                        logger.info(f"Sent {total_sent} bytes so far...")

                logger.info(f"File {file_name} sent successfully!")
        except Exception as e:
            logger.error(f"Error sending file: {e}")