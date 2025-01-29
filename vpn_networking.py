import socket
import os
import threading
import netifaces
import requests
import subprocess



# URL for the Flask server
url = "http://34.60.27.56:5000"



def vpn_server_connection():
    print("[DEBUG] Checking if wg0.conf exists...")
    if os.path.exists("/etc/wireguard/wg0.conf"):
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
    else:
        print("[ERROR] Config file not found.")
        return False


def vpn_server_disconnection():
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
    try:
        addrs = netifaces.ifaddresses(interface)
        ip_info = addrs[netifaces.AF_INET][0]  # Get IPv4 address
        return ip_info['addr']
    except KeyError:
        return f"Interface {interface} not found or has no IP!"


LISTENING_PORT = 5001
BUFFER_SIZE = 1024



def send_auth_details(username:str, password:str):

    """Send authentication details to the server."""

    print("Ready to Send")

    data = {"username": username, "password": password}
    auth_server_url = f"{url}/auth"

    try:
        response = requests.post(auth_server_url, json=data)
        print("try1")
        response.raise_for_status()  # Raise exception for HTTP error codes
        print("try2")
        print("Authentication Successful!")
        print("try3")
        print("Available Users:", response.json()["users"])
        print("try4")
        return response.json()["users"].split(", ") # this will return a list of users
        print("try5")
    except requests.exceptions.RequestException as e:
        print("Authentication Failed! Error:", str(e))
        return None  # Return None for any failure
    except KeyError:
        print("Unexpected response format from server.")
        return None

def user_ip_retrival(receiver_username:str):

    global url;
    data = {"receiver_name": receiver_username}
    # Sending the request
    user_ip_server_url = f"{url}/receiver_selection"
    # response = requests.post(url, json=data)

    try:
        # Sending the request
        response = requests.post(user_ip_server_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Process the response
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

def get_public_key(receiver_username:str):

    global url;
    data = {"receiver_name": receiver_username}
    # Sending the request
    public_key_url = f"{url}/public_key"
    # response = requests.post(url, json=data)

    try:
        # Sending the request
        response = requests.post(public_key_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Process the response
        receiver_public_key = response.json().get("receiver_public_key")
        if receiver_public_key:
            print("Receiver Found!")
            print("Receiver Static IP:", receiver_public_key)
            return receiver_public_key
        else:
            print("Receiver public key not found or unexpected response format.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Receiver public key retreval Failed! Error: {e}")
        return None
    except KeyError:
        print("Unexpected response format from server.")
        return None
