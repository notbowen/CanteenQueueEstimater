from tkinter import *
import tkinter as tk

stall_name = ["Drinks", "Snacks", "Malay 1", "Malay 2", "Western", "Chicken Rice", "Oriental Taste", "CLOSED"]

displayed = {}

#Create main window
root = tk.Tk()

#Create WidgetWrapper
widgetWrapper = tk.Text(root, wrap="char", borderwidth=0,highlightthickness=0,state="disabled", cursor="arrow") 
#state = "disabled" is to disable text from being input by user
#cursor = "arrow" is to ensure when user hovers, the "I" beam cursor (text cursor) is not displayed

widgetWrapper.pack(fill="both", expand=True)

def additem(i):
    item = Label(bd = 5, relief="solid", text=f"{stall_name[i]}:\n\n               WATITING TIME               \nmins", font=('Arial', 25), bg="white") #Create the actual widgets
    displayed[stall_name[i]] = item
    widgetWrapper.window_create("end", window=item) #Put it inside the widget wrapper (the text)

# add a few boxes to start
for i in range(8):
    additem(i)

root.mainloop()