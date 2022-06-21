# server.py
# In charge of accepting RPI connections and
# updating the wait time GUI

# Libraries
import tkinter as tk
import threading
import socket

import time

# Variables
debug = True

server_ip = "127.0.0.1"
server_port = 6942

stall_name = ["Drinks", "Snacks", "Malay 1", "Malay 2", "Western", "Chicken Rice", "Oriental Taste", "CLOSED"]
displayed = {}  # Format: [<Tkinter Label Class>, <Last Updated Time (int)>]
max_clients = 8

last_update_threshold = 60

password = "YW1vZ3Vz"

# Debug print
def debug_print(msg):
    if debug:
        print(msg)
 
#output preprocessor
def output_preprocessor(input_time):
  input_time=int(input_time)
  input_time*=2
  rounded_time=math.ceil(input_time)
  rounded_time/=2
  if rounded_time%1==0.5:
    output_str="~"+str(rounded_time//1)+" mins 30 seconds"
  else:
    output_str="~"+str(rounded_time//1)+" mins 00 seconds"
  return output_str
        
# Init GUI
def init_GUI():
    root = tk.Tk()

    widgetWrapper = tk.Text(root, wrap="char", borderwidth=0,highlightthickness=0,state="disabled", cursor="arrow") 
    widgetWrapper.pack(fill="both", expand=True)

    def additem(i):
        item = tk.Label(bd = 5, relief="solid", text=f"{stall_name[i]}:\n\n               WAITING TIME               \nmins", font=('Arial', 25), bg="white") #Create the actual widgets
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
    
    display_waiting_time=output_preprocessor(waiting_time)

    displayed[stall][0].config(text=f"{stall}:\n\n               {display_waiting_time}               \nmins\n")

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
