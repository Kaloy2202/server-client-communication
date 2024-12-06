import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import random

def append_crc(message):
    generator = '10011'
    message = ''.join(format(ord(char), '08b') for char in message)
    k = len(message)
    n = len(generator) - 1
    padded_message = message + '0' * n
    remainder = modulo2_division(padded_message, generator)
    transmitted_message = message + remainder

    # Simulate a 5% chance of error
    if random.random() < 0.05:
        bit_to_flip = random.randint(0, len(transmitted_message) - 1)
        transmitted_message = (
            transmitted_message[:bit_to_flip] +
            ('1' if transmitted_message[bit_to_flip] == '0' else '0') +
            transmitted_message[bit_to_flip + 1:]
        )

    return transmitted_message

def validate_crc(received_message):
    try:
        generator = '10011'
        k = len(received_message) - (len(generator) - 1)
        original_message = received_message[:k]
        remainder = modulo2_division(received_message, generator)
        is_valid = int(remainder) == 0
        return is_valid, original_message
    except Exception as e:
        print(f"[ERROR] CRC validation failed: {e}")
        return False, ""


def modulo2_division(dividend, divisor):
    n = len(divisor)
    remainder = list(dividend[:n])
    for i in range(n, len(dividend) + 1):
        if remainder[0] == '1':  # Perform XOR if the first bit is 1
            for j in range(1, n):
                remainder[j] = '0' if remainder[j] == divisor[j] else '1'
        remainder = remainder[1:]  # Drop the used bit
        if i < len(dividend):
            remainder.append(dividend[i])
    return ''.join(remainder)

# Server configuration
HOST = '0.0.0.0'  # Localhost; use server IP if on a netwo
PORT = 5555

# Set up the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

clients = []
nicknames = []

# GUI setup for the server
server_root = tk.Tk()
server_root.title("Server Chat")

# Chat display area
chat_display = scrolledtext.ScrolledText(server_root, state='disabled')
chat_display.pack(padx=20, pady=5)

# Message input field
message_entry = tk.Entry(server_root, width=50)
message_entry.pack(padx=20, pady=5)

# Function to update chat display
def update_chat(message):
    chat_display.config(state='normal')
    chat_display.insert(tk.END, message + '\n')
    chat_display.yview(tk.END)
    chat_display.config(state='disabled')

# Function to broadcast messages to all clients
def broadcast(message):
    if isinstance(message, str):
        message = message.encode('utf-8')  # Ensure bytes
    print(f"[DEBUG] Broadcasting: {message.decode('utf-8')}")
    for client in clients:
        try:
            client.send(message)
        except Exception as e:
            print(f"[ERROR] broadcast: {e}")



# Function to handle each client
def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                raise ConnectionResetError  # Handle clean disconnects
            update_chat(message.decode('utf-8'))
            broadcast(message)
        except Exception as e:
            index = clients.index(client)
            nickname = nicknames[index]
            clients.remove(client)
            nicknames.remove(nickname)
            client.close()
            print(f"[ERROR] Client {nickname} disconnected: {e}")
            broadcast(f"{nickname} has left the chat.".encode('utf-8'))
            update_chat(f"{nickname} has left the chat.")
            break


# Function to accept clients and start their threads
def receive_clients():
    while True:
        client, address = server_socket.accept()
        update_chat(f"Connected with {str(address)}")

        # Get nickname and add client
        client.send("Nickname: ".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        update_chat(f"Nickname of the client is {nickname}")
        broadcast(f"{nickname} joined the chat!".encode('utf-8'))
        client.send("Connected to the server!".encode('utf-8'))

        # Start thread to handle client
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

# Function to send server messages
def send_server_message():
    message = message_entry.get()
    message_entry.delete(0, tk.END)
    if message:
        formatted_message = f"Server: {message}"
        update_chat(formatted_message)
        broadcast(formatted_message.encode('utf-8'))

# Send button for server GUI
send_button = tk.Button(server_root, text="Send", command=send_server_message)
send_button.pack(pady=5)

# Start receiving clients in a separate thread
receive_thread = threading.Thread(target=receive_clients)
receive_thread.start()

# Run the server GUI
server_root.mainloop()
