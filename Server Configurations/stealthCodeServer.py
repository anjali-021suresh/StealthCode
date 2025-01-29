from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_FILE = "users.db"
PUBLIC_KEY_REGISTERY = "public_key.db"


@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # input validation
    if not username or not password:
        return jsonify({"status": "failure", "message": "Username and password are required"}), 400
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone() # fetches one row
    cursor.execute("SELECT username FROM users WHERE username != ?;", (username,)) # giving list of avilable users to communicate
    usernames = cursor.fetchall()
    connection.close()

    usernames = [row[0] for row in usernames]
    usernames_str = ", ".join(usernames)

    if result and result[0] == password:
        return jsonify({"status": "success", "users": usernames_str}), 200
    else:
        return jsonify({"status": "failure", "message": "Invalid username or password"}), 401
    
@app.route('/receiver_selection', methods=['POST'])
def receiver_selection():
    data = request.json
    receiver_name = data.get("receiver_name")

    # input validation
    if not receiver_name:
        return jsonify({"status": "failure", "message": "receiver name is required"}), 400
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT static_ip_address FROM users WHERE username = ?", (receiver_name,))
    result = cursor.fetchone() # fetches one row
    receiver_static_ip = result[0]

    return jsonify({'status': 'success', 'receiver_static_ip': receiver_static_ip}), 200


@app.route('/public_key', methods=['POST'])
def public_key_registery():
    data = request.json
    receiver_name = data.get("receiver_name")

    # input validation
    if not receiver_name:
        return jsonify({"status": "failure", "message": "receiver name is required"}), 400
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT public_key FROM public_key WHERE username = ?", (receiver_name,))
    result = cursor.fetchone() # fetches one row
    reciever_public_key = result[0]

    return jsonify({'status': 'success', 'reciever_public_key': reciever_public_key}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
