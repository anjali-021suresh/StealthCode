from flask import Flask, request, jsonify
import sqlite3

import traceback

app = Flask(__name__)

DB_FILE = "users.db"
PUBLIC_KEY_REGISTRY = "public_key.db" # encrpytion decrption pub key


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


@app.route('/add_public_key', methods=['POST'])
def submit_public_key():
    data = request.json
    username = data.get("username")
    public_key = data.get("public_key")

    if not username:
        return jsonify({"status": "failure", "message": "Username is required"}), 400

    try:
        # Connect to the database
        connection = sqlite3.connect(PUBLIC_KEY_REGISTRY)
        cursor = connection.cursor()

        # Update the public key for the given username
        cursor.execute("UPDATE public_key SET public_key = ? WHERE username = ?", (public_key, username))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'status': 'failure', 'message': 'Receiver not found'}), 404

        return jsonify({'status': 'success', 'message': 'Public key updated successfully'}), 200

    except sqlite3.Error as e:
        print("Database Error:", str(e))  # Log the error
        print(traceback.format_exc())  # Print the full traceback
        return jsonify({'status': 'failure', 'message': str(e)}), 500

    finally:
        connection.close()


@app.route('/get_public_key', methods=['POST'])
def get_public_key():
    data = request.json
    receiver_name = data.get("receiver_name")

    # Input validation
    if not receiver_name:
        return jsonify({"status": "failure", "message": "Receiver name is required"}), 400

    try:
        # Connect to the database
        connection = sqlite3.connect(PUBLIC_KEY_REGISTRY)  # Ensure variable is correctly defined
        cursor = connection.cursor()

        # Retrieve the public key for the given username
        cursor.execute("SELECT public_key FROM public_key WHERE username = ?", (receiver_name,))
        result = cursor.fetchone()

        if result is not None:  # Ensures we don't access NoneType
            receiver_public_key = result[0]
            return jsonify({'status': 'success', 'receiver_public_key': receiver_public_key}), 200
        else:
            return jsonify({'status': 'failure', 'message': 'Receiver not found'}), 404

    except sqlite3.Error as e:
        return jsonify({'status': 'failure', 'message': str(e)}), 500

    finally:
        connection.close()  # Ensure database connection is closed





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
