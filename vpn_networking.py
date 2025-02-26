import os
import netifaces
import requests
import subprocess
from datetime import datetime

# URL for the Flask server
URL = "http://34.60.27.56:5000"
LISTENING_PORT = 5001
BUFFER_SIZE = 4096

def vpn_server_connection():
    """Connect to the VPN server using WireGuard."""
    print("[DEBUG] Checking if wg0.conf exists...")
    if not os.path.exists("/etc/wireguard/wg0.conf"):
        print("[ERROR] Config file not found.")
        return False

    print("[DEBUG] Config file exists. Attempting to bring up WireGuard...")
    result = subprocess.run(
        ["sudo", "wg-quick", "up", "/etc/wireguard/wg0.conf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("[DEBUG] Output:", result.stdout)
    print("[DEBUG] Errors:", result.stderr)

    if result.returncode == 0:
        print("[DEBUG] WireGuard started successfully.")
        return True
    else:
        print("[ERROR] Failed to start WireGuard.")
        return False

def vpn_server_disconnection():
    """Disconnect from the VPN server."""
    try:
        result = subprocess.run(
            ["sudo", "wg-quick", "down", "/etc/wireguard/wg0.conf"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("[INFO] VPN disconnected successfully.")
        print("[DEBUG] Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to disconnect VPN.")
        print("[DEBUG] Error Output:", e.stderr)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

def get_wireguard_ip(interface="wg0"):
    """Retrieve the IP address of the WireGuard interface."""
    try:
        addrs = netifaces.ifaddresses(interface)
        ip_info = addrs[netifaces.AF_INET][0]  # Get IPv4 address
        return ip_info['addr']
    except KeyError:
        return f"Interface {interface} not found or has no IP!"

def send_auth_details(username: str, password: str):
    """Send authentication details to the server."""
    data = {"username": username, "password": password}
    auth_server_url = f"{URL}/auth"

    try:
        response = requests.post(auth_server_url, json=data)
        response.raise_for_status()  # Raise exception for HTTP error codes
        print("Authentication Successful!")
        print("Available Users:", response.json()["users"])
        return response.json()["users"].split(", ")  # Return a list of users
    except requests.exceptions.RequestException as e:
        print("Authentication Failed! Error:", str(e))
        return None  # Return None for any failure
    except KeyError:
        print("Unexpected response format from server.")
        return None

def user_ip_retrieval(receiver_username: str):
    """Retrieve the IP address of the receiver."""
    data = {"receiver_name": receiver_username}
    user_ip_server_url = f"{URL}/receiver_selection"

    try:
        response = requests.post(user_ip_server_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        receiver_static_ip = response.json().get("receiver_static_ip")
        if receiver_static_ip:
            print("Receiver Found!")
            print("Receiver Static IP:", receiver_static_ip)
            return receiver_static_ip
        else:
            print("Receiver not found or unexpected response format.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Receiver Selection Failed! Error: {e}")
        return None
    except KeyError:
        print("Unexpected response format from server.")
        return None

def get_public_key(receiver_username: str):
    """Retrieve the public key of the receiver."""
    data = {"receiver_name": receiver_username}
    public_key_url = f"{URL}/get_public_key"

    try:
        response = requests.post(public_key_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        receiver_public_key = response.json().get("receiver_public_key")
        if receiver_public_key:
            print("Receiver Found!")
            print("Receiver public key found:", receiver_public_key)
            return receiver_public_key
        else:
            print("Receiver public key not found or unexpected response format.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Receiver public key retrieval Failed! Error: {e}")
        return None
    except KeyError:
        print("Unexpected response format from server.")
        return None


def send_public_key(public_key, username):
    """Send the public key of the user to update it in the database."""
    data = {"username": username, "public_key": public_key}
    public_key_url = f"{URL}/add_public_key"

    try:
        response = requests.post(public_key_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        if response.status_code == 200:
            print("Update successful")
            return True
        else:
            print(f"Username not found or unexpected response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Public key update failed! Error: {e}")
        return False
