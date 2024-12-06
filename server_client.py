import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Server configuration
HOST = '127.0.0.1'  # Localhost; use server IP if on a network
PORT = 5555

# Cyclic Redundancy Check
GENERATOR = '10101'  # Generator polynomial G(X) = x^4 + x + 1

# Convert message to ASCII binary representation
def message_to_binary(message):
    return ''.join(format(ord(c), '08b') for c in message)

# Convert ASCII binary representation back to message
def binary_to_message(binary_string):
    # Ensure binary string length is a multiple of 8
    if len(binary_string) % 8 != 0:
        raise ValueError("Binary string must be a multiple of 8 bits")
    
    # Convert binary back to ASCII characters
    return ''.join(chr(int(binary_string[i:i+8], 2)) for i in range(0, len(binary_string), 8))

def crc_decode(received_message):
    """
    Decode and verify message using CRC
    Return True if no errors detected, False otherwise
    """
    if len(received_message) < 4:
        return False
    
    message = received_message[:-4]
    received_crc = received_message[-4:]
    
    # Append 4 zero bits
    extended_message = message + '0000'
    
    # Convert to list for easier manipulation
    message_bits = list(extended_message)
    generator_bits = list(GENERATOR)
    
    # Perform modulo-2 division
    for i in range(len(message_bits) - len(generator_bits) + 1):
        if message_bits[i] == '1':
            for j in range(len(generator_bits)):
                message_bits[i + j] = str(int(message_bits[i + j]) ^ int(generator_bits[j]))
    
    # Check if remainder matches received CRC
    return ''.join(message_bits[-4:]) == received_crc

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
    for client in clients:
        client.send(message)

# Function to handle each client
def handle_client(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            
            # Split nickname and transmitted message
            parts = message.split(': ', 1)
            if len(parts) < 2:
                update_chat(message)
                
            nickname, transmitted_message = parts
            
            # Check if CRC is valid
            if crc_decode(transmitted_message):
                # Remove CRC bits
                binary_message = transmitted_message[:-4]
                
                # Convert binary back to readable message
                decoded_message = binary_to_message(binary_message)
                
                # Format and broadcast
                formatted_message = f"{nickname}: {decoded_message}"
                update_chat(formatted_message)
                broadcast(formatted_message.encode('ascii'))
            else:
                update_chat("Received message with CRC error.")
        
        except:
            # Handle client disconnection
            index = clients.index(client)
            nickname = nicknames[index]
            clients.remove(client)
            nicknames.remove(nickname)
            client.close()
            broadcast(f"{nickname} has left the chat.".encode('ascii'))
            update_chat(f"{nickname} has left the chat.")
            break

# Function to accept clients and start their threads
def receive_clients():
    while True:
        client, address = server_socket.accept()
        update_chat(f"Connected with {str(address)}")

        # Get nickname and add client
        client.send("Nickname: ".encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)

        update_chat(f"Nickname of the client is {nickname}")
        broadcast(f"{nickname} joined the chat!".encode('ascii'))
        client.send("Connected to the server!".encode('ascii'))

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
        broadcast(formatted_message.encode('ascii'))

# Send button for server GUI
send_button = tk.Button(server_root, text="Send", command=send_server_message)
send_button.pack(pady=5)

# Start receiving clients in a separate thread
receive_thread = threading.Thread(target=receive_clients)
receive_thread.start()

# Run the server GUI
server_root.mainloop()