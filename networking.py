import os
import socket
import threading
import time
from datetime import datetime

class Networking:

    def __init__(self):
        self.LISTEN_PORT = 5001
        self.HOST_IP = "10.10.0.2"  # Bind to all available interfaces
        self.BUFFER_SIZE = 4096  # Size of each chunk sent
        self.SAVE_PATH = "received_files"  # Directory to save received files
        self.server_socket = None
        self.is_running = False


    def start_server(self):
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
        try:
            # Receive file name
            file_name = conn.recv(self.BUFFER_SIZE).decode("utf-8")
            print(f"[+] Receiving file: {file_name}")

            def get_file_type(file_name):
                _, file_extension = os.path.splitext(file_name)  # Get the file extension
                return file_extension.lower()  # Return the extension in lowercase for consistency

            # if json file then store the key to temp.
            file_type = get_file_type(file_name)
            if file_type == ".json":
                location_path = f"/tmp/{file_name}"
                with open(location_path, "wb") as file:
                    while True:
                        data = conn.recv(self.BUFFER_SIZE)
                        if not data:  # Break when no more data is sent
                            break
                        file.write(data)
            else :
                # Open a file to save the incoming data
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                save_path = os.path.join(self.SAVE_PATH, f"{timestamp}_{file_name}")
                with open(save_path, "wb") as file:
                    while True:
                        data = conn.recv(self.BUFFER_SIZE)
                        if not data:  # Break when no more data is sent
                            break
                        file.write(data)

            print(f"[+] File received successfully: {save_path}")

        except Exception as e:
            print(f"[-] Error receiving file: {e}")
        finally:
            conn.close()

    def stop_server(self):
        print("[*] Stopping server...")
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        print("[*] Server stopped.")

    def send_file(self, file_path, dest_ip):
        if not os.path.isfile(file_path):
            print(f"[-] File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        print(f"[*] Connecting to server at {dest_ip}:{self.LISTEN_PORT}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((dest_ip, self.LISTEN_PORT))
                print("[+] Connected to server")

                # Send file name
                client_socket.send(file_name.encode("utf-8"))

                # Send file data
                with open(file_path, "rb") as file:
                    while chunk := file.read(self.BUFFER_SIZE):
                        client_socket.send(chunk)

                print(f"[+] File {file_name} sent successfully!")
        except Exception as e:
            print(f"[-] Error sending file: {e}")


    


if __name__ == "__main__":
    network = Networking()
    mode = input("Enter mode (server/client): ").strip().lower()

    if mode == "server":
        server_thread = threading.Thread(target=network.start_server)
        server_thread.start()

        try:
            while True:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("\n[!] Stopping server...")
            network.stop_server()
            server_thread.join()
    elif mode == "client":
        file_path = input("Enter file path to send: ").strip()
        dest_ip = input("Enter destination IP: ").strip()
        network.send_file(file_path, dest_ip)
    else:
        print("[-] Invalid mode. Use 'server' or 'client'.")
