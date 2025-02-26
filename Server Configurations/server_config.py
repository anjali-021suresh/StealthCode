import os
import subprocess
import sqlite3
import json
import requests


WG_CONFIG_PATH = "/etc/wireguard/wg0.conf"
PRIVATE_KEY_PATH = "/etc/wireguard/server_private_key.key"
PUBLIC_KEY_PATH = "/etc/wireguard/server_public_key.key"
VPN_SUBNET = "10.10.0.0/24"
SERVER_IP = "10.10.0.1/24"
LISTEN_PORT = "51820"
POST_UP = "iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -o eth0 -j MASQUERADE"

POST_DOWN = "iptables -t nat -D POSTROUTING -s 10.10.0.0/24 -o eth0 -j MASQUERADE"
response = requests.get("https://ifconfig.me")
SERVER_PUBLIC_IP = response.text.strip()


def run_command(command, sudo=True):
    if sudo:
        command = f"sudo bash -c \"{command}\""

    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        exit(1)


# Step 4: Enable IP forwarding
def enable_ip_forwarding():
    print("[+] Enabling IP forwarding...")
    run_command("sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf", sudo=True)
    run_command("sysctl -p", sudo=True)

# Step 5: Start WireGuard
def start_wireguard():
    print("[+] Starting WireGuard...")
    run_command(f"wg-quick up {WG_CONFIG_PATH}", sudo=True)
    run_command(f"systemctl enable wg-quick@wg0", sudo=True) # for stating it in boot up time



def server_side_vpn_config():

    print("[+] Installing WireGuard...")
    run_command("apt update && apt upgrade -y", sudo=True)
    run_command("apt install wireguard", sudo=True)

    #2> Generating server keys.
    print("[+] Generating WireGuard keys...")
    command = (
        "sudo sh -c 'umask 077 && wg genkey | tee /etc/wireguard/server_private_key.key | "
        "wg pubkey > /etc/wireguard/server_public_key.key'"
    )
    subprocess.run(command, shell=True, check=True)
    print("[+] WireGuard keys generated successfully.")

    #3> Generating wireguard config file
    print("[+] Creating WireGuard configuration...")
    with open(PRIVATE_KEY_PATH, "r") as file:
        private_key = file.read().strip()

    wg_config = f"""[Interface]
    PrivateKey = {private_key}
    Address = {SERVER_IP}
    ListenPort = {LISTEN_PORT}

    PostUp = {POST_UP}
    PostDown = {POST_DOWN}"""
    # Write configuration to wg0.conf
    with open("/tmp/wg0.conf", "w") as f:
        f.write(wg_config)

    # Move config to WireGuard directory
    run_command(f"mv /tmp/wg0.conf {WG_CONFIG_PATH}", sudo=True)
    run_command(f"chmod 600 {WG_CONFIG_PATH}", sudo=True)

    enable_ip_forwarding()
    start_wireguard()



def public_key_db(client_name, public_key:None):

    connection = sqlite3.connect("public_key.db")
    cursor = connection.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS public_key(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                public_key TEXT UNIQUE
                            );
                            """)
    
    cursor.execute("""INSERT INTO public_key 
                   (username, public_key) VALUES 
                   (?, ?);
                    """, (client_name, public_key))
    
    connection.commit()
    connection.close()


def add_clients(client_name):

    print(f"[+] Adding client {client_name}...")
    ip_address = allocate_static_ip()

    run_command(f"umask 077 && wg genkey | tee '/tmp/{client_name}_private.key' | wg pubkey > '/tmp/{client_name}_public.key'", sudo=True)
    
    # Reading public and private keys
    with open(f"/tmp/{client_name}_private.key", "r") as f:
        client_private_key = f.read().strip()

    with open(f"/tmp/{client_name}_public.key", "r") as f:
        client_public_key = f.read().strip()

    # Add client configuration to wg0.conf
    peer_config = f"""[Peer]
    PublicKey = {client_public_key}
    AllowedIPs = {ip_address}/32"""

    with open(WG_CONFIG_PATH, "a") as f:
        f.write(peer_config)

    # Restart WireGuard to apply changes
    run_command(f"wg set wg0 peer {client_public_key} allowed-ips {ip_address}/32", sudo=True)

    # Generate client config file
    client_config = f"""[Interface]
    PrivateKey = {client_private_key}
    Address = {ip_address}/24
    DNS = 8.8.8.8

[Peer]
    PublicKey = {open(PUBLIC_KEY_PATH).read().strip()}
    Endpoint = {SERVER_PUBLIC_IP}:51820
    AllowedIPs = 0.0.0.0/0
    PersistentKeepalive = 25"""
    
    with open(f"/tmp/{client_name}_wg0.conf", "w") as f:
        f.write(client_config)
    
    print(f"[+] Client configuration saved to /tmp/{client_name}_wg0.conf")
    public_key_db(client_name, client_public_key)
    print(f"[+] Public key is added to the database public_key_registery")
    return ip_address
    
    
def allocate_static_ip():

    connection = sqlite3.connect("ip_allocation.db")
    cursor = connection.cursor()
    cursor.execute("""SELECT ip_address FROM ip_allocations 
                   WHERE assigned = 0 LIMIT 1;
                   """)
    result = cursor.fetchone()

    if result:
        ip_address = result[0]
        cursor.execute("""UPDATE ip_allocations 
                       SET assigned = 1 
                       WHERE ip_address = ?""", (ip_address,))
        connection.commit()
        connection.close()
        return ip_address
    else :
        connection.close()
        raise Exception("No available IP addresses!")




def init_dbs():

    # 1. Connection setup
    connection = sqlite3.connect("users.db")
    connection2 = sqlite3.connect("ip_allocation.db")

    # 2. Create a cursor object to execute SQL commands
    cursor = connection.cursor()
    cursor2 = connection2.cursor()

    # 3. getting the schema
    with open('schema.sql', 'r') as schema:
        create_table_query = schema.read()

    create_table_query_ip = """CREATE TABLE IF NOT EXISTS ip_allocations(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                ip_address TEXT UNIQUE NOT NULL,
                                assigned INTEGER DEFAULT 0
                            );
                            """


    # 4. execute the create table query
    cursor.execute(create_table_query)
    cursor2.execute(create_table_query_ip)

    # 5. Commit changes
    connection.commit()
    connection2.commit()

    # Pre-Initialisation of ip address
    cursor2.execute("SELECT COUNT(*) FROM ip_allocations")
    if cursor2.fetchone()[0] == 0:
        ip_base = "10.10.0."
        for i in range(2, 255):  # 10.10.0.2 to 10.10.0.254
            cursor2.execute("""INSERT INTO ip_allocations 
                            (ip_address) 
                            VALUES (?)""", (f"{ip_base}{i}",))
        connection2.commit()
    
    # 6. Close the connection
    connection2.close()
    connection.close()





def users_setup():


    # 1. Connection setup
    connection = sqlite3.connect("users.db")

    # 2. Create a cursor object to execute SQL commands
    cursor = connection.cursor()

    # 3. getting the user details
    with open("user_data.json", "r") as json_file:
        user_data = json.load(json_file)

    # 4. inserting user data into the database
    for user in user_data:

        # 1. need to generate client config file and add the static ip to database
        ip_address = add_clients(user["username"])
        cursor.execute("""INSERT INTO users
                       (username, password, static_ip_address) 
                       VALUES(?, ?, ?);
                       """, (user['username'], user['password'], ip_address))
        
    # 5. Commiting and closing the connection
    connection.commit()
    connection.close()



    


if __name__ == '__main__':

    # 1> Database inits
    init_dbs()
    # 2> Server Configurations
    server_side_vpn_config()
    # 3> User Setups and configurations as per no of avilable ips and users.
    users_setup()


