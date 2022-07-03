# server.py
# In charge of accepting RPI connections and
# updating the wait time GUI

# Libraries
import tkinter as tk
import threading
import socket

import argparse
import os
import time
import sys

import requests

# Parse Arguments
parser = argparse.ArgumentParser(description='Socket Server for Canteen Queue Counter')
parser.add_argument('--debug', default=False, action="store_true", help='Turns on debug logging')
parser.add_argument('--url', type=str, default="http://localhost", help='URL of Flask Server')
parser.add_argument('--ip', type=str, default="0.0.0.0", help='IP Address of Socket Server')
parser.add_argument('--port', type=int, default=6942, help='Port of Socket Server')
args = parser.parse_args()

# Variables
debug = args.debug

server_ip = args.ip
server_port = args.port

url = args.url

# Read Credentials
cred_path = os.path.join(os.path.dirname(__file__), "../misc/credentials.txt")
credentials = {}

with open(cred_path, "r") as f:
    for line in f:
       (key, val) = line.split("=")
       credentials[key] = val
    f.close()

try:
    password = credentials["password"].strip("\n")
    auth_key = credentials["auth_key"].strip("\n")
    auth_token = credentials["auth_token"].strip("\n")
except KeyError:
    print("[FATAL] Missing credentials in credentials.txt")
    sys.exit(1)

stall_name = ["Drinks", "Snacks", "Malay 1", "Malay 2", "Western", "Chicken Rice", "Oriental Taste", "CLOSED"]
displayed = {}  # Format: [<Tkinter Label Class>, <Last Updated Time (int)>]
max_clients = 8

last_update_threshold = 60

# Debug print
def debug_print(msg):
    if debug:
        print(msg)

# Init GUI
def init_GUI():
    root = tk.Tk()

    widgetWrapper = tk.Text(root, wrap="char", borderwidth=0, highlightthickness=0, state="disabled", cursor="arrow") 
    widgetWrapper.pack(fill="both", expand=True)

    def additem(i):
        item = tk.Label(bd = 5, relief="solid", text=f"{stall_name[i]}:\n\n               ???               \nmins", font=('Arial', 25), bg="white") #Create the actual widgets
        displayed[stall_name[i]] = [item, 0]
        widgetWrapper.window_create("end", window=item)

    for i in range(8):
        additem(i)

    root.mainloop()

# Update last updated time
def last_update_updater():
    while True:
        time.sleep(1)
        # Key is stall name, value is [<Tkinter Label Class>, <Last Updated Time (int)>]
        for key, value in displayed.items():
            value[1] += 1

            if value[1] >= last_update_threshold:
                value[0].config(text=f"{key}:\n\n               ???               \nmins\n")

# On Recv Data function
def on_recv_data(c, addr):
    # Get data
    data = c.recv(1024).decode()
    data = data.split("|")

    # Check if data is valid
    if (data[0] != password or len(data) != 3 or data[1] not in stall_name):
        print("[ERROR] Invalid data received!")
        c.send(b"ACK")
        c.close()
        return

    # Update GUI from data
    stall = data[1]
    waiting_time = data[2]

    displayed[stall][0].config(text=f"{stall}:\n\n               {waiting_time}               \nmins\n")

    # Update Flask server
    authentication = {auth_key: auth_token}

    try:
        r = requests.post(url + f"/api/update_timing?stall_name={stall}&queue_time={waiting_time}", headers=authentication)
        if r.status_code != 200:
            print("[ERROR] Received status code: " + str(r.status_code) + " from server!")
            print("[ERROR] Response: " + str(r.text))
    except Exception as e:
        print("[ERROR] Failed to send data to server!")
        print("Error Log: " + str(e))

    # Reset Last Updated Time
    displayed[stall][1] = 0

    # Send ACK
    c.send(b"ACK")
    c.close()

    return

# Main Server function
def main():
    # Init GUI thread
    init_GUI_thread = threading.Thread(target=init_GUI)
    init_GUI_thread.start()

    time.sleep(1)

    # Start last updated time updater thread
    last_update_updater_thread = threading.Thread(target=last_update_updater)
    last_update_updater_thread.start()

    # Create socket
    try:
        print("[INFO] Creating socket...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((server_ip, server_port))
        s.listen(max_clients)
        print("[INFO] Socket created at " + server_ip + ":" + str(server_port))
    except Exception as e:
        print("[FATAL] Socket Creation Failed!")
        print("Error Log: " + str(e))
        return

    # Accept connections
    while True:
        c, addr = s.accept()
        debug_print("[DEBUG] Accepted connection from " + str(addr))
        thread = threading.Thread(target=on_recv_data, args=(c, addr))
        thread.daemon = True
        thread.start()

# Run
if __name__ == "__main__":
    main()