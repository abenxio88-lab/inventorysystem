"""
TEST - Does Tkinter work at all?
"""
import tkinter as tk
from tkinter import ttk, messagebox

print("Creating window...")

root = tk.Tk()
root.title("TEST WINDOW")
root.geometry("400x300")

label = ttk.Label(root, text="✅ IF YOU SEE THIS, TKINTER WORKS!\n\nClose this and run main_simple.py", 
                  font=("Segoe UI", 14), justify="center")
label.pack(expand=True)

def close_and_run_main():
    root.destroy()
    print("Test window closed - now running main app...")
    import main_simple

button = ttk.Button(root, text="Close & Run Main App", command=close_and_run_main)
button.pack(pady=20)

print("Window created - should be visible now!")
root.mainloop()
print("Window closed.")
