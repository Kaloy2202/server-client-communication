import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext

# Client Configuration
HOST = '10.74.0.95'  # Should match the server's IP
PORT = 5555

# Set up the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# GUI Setup
root = tk.Tk()
root.withdraw()  # Hide the main window initially

# Prompt for nickname
nickname = simpledialog.askstring("Nickname", "Please enter your nickname:", parent=root)

# Ensure nickname is provided
if not nickname:
    root.quit()
else:
    client_socket.send(nickname.encode('utf-8'))

    # Show main chat window
    root.deiconify()
    root.title(f"{nickname}'s Chat")

    # Chat window
    chat_window = scrolledtext.ScrolledText(root, state='disabled')
    chat_window.pack(padx=20, pady=5)

    # Input field
    message_field = tk.Entry(root, width=50)
    message_field.pack(padx=20, pady=5)

    # Function to update chat window
    def update_chat(message):
        chat_window.config(state='normal')
        chat_window.insert(tk.END, message + '\n')
        chat_window.yview(tk.END)
        chat_window.config(state='disabled')

    # Function to send messages
    def send_message():
        message = message_field.get()
        message_field.delete(0, tk.END)

        if message:
            formatted_message = f"{nickname}: {message}"
            client_socket.send(formatted_message.encode('utf-8'))

    # Function to leave the chat and close the GUI
    def leave_chat():
        client_socket.send(f"{nickname} has left the chat.".encode('utf-8'))
        client_socket.close()
        root.quit()  # Closes the GUI

    # Send button for client GUI
    send_button = tk.Button(root, text="Send", command=send_message)
    send_button.pack(pady=5)

    # Leave button to exit the chat
    leave_button = tk.Button(root, text="Leave", command=leave_chat)
    leave_button.pack(pady=5)

    # Listen for incoming messages
    def receive_messages():
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                update_chat(message)
            except:
                update_chat("You have been disconnected.")
                client_socket.close()
                break

    # Start the receive thread
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()

    # Handle window close
    def on_closing():
        leave_chat()

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Trigger leave_chat when window closes
    root.mainloop()
