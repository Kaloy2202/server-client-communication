import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import random

# Client Configuration
HOST = '127.0.0.1'  # Should match the server's IP
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

def crc_encode(binary_message):
    """
    Encode binary message using CRC
    1. Append n (4) zero bits to message
    2. Perform modulo-2 division
    3. Return the remainder (CRC)
    """
    # Append 4 zero bits (n bits from generator polynomial)
    extended_message = binary_message + '0000'
    
    # Convert to list for easier manipulation
    message_bits = list(extended_message)
    generator_bits = list(GENERATOR)
    
    # Perform modulo-2 division
    for i in range(len(message_bits) - len(generator_bits) + 1):
        if message_bits[i] == '1':
            for j in range(len(generator_bits)):
                message_bits[i + j] = str(int(message_bits[i + j]) ^ int(generator_bits[j]))
    
    # Last 4 bits are the CRC remainder
    return ''.join(message_bits[-4:])

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
    client_socket.send(nickname.encode('ascii'))

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

        # Convert message to binary
        binary_message = message_to_binary(message)
        
        # Encode message with CRC
        crc_remainder = crc_encode(binary_message)
        transmitted_message = binary_message + crc_remainder
        
        # 5% chance to add a random bit
        if random.random() < 0.05:
            bit_to_add = '1' if random.random() < 0.5 else '0'
            transmitted_message += bit_to_add
        
        # Format and send
        formatted_message = f"{nickname}: {transmitted_message}"
        client_socket.send(formatted_message.encode('ascii'))

    # Function to leave the chat and close the GUI
    def leave_chat():
        client_socket.send(f"{nickname} has left the chat.".encode('ascii'))
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
                message = client_socket.recv(1024).decode('ascii')
                
                # Split nickname and transmitted message
                parts = message.split(': ', 1)
                
                # Check if it's a server message
                if parts[0] == 'Server':
                    update_chat(message)
                    continue
                
                nickname, transmitted_message = parts

                # Check if CRC is valid
                if crc_decode(transmitted_message):
                    # Remove CRC bits
                    binary_message = transmitted_message[:-4]

                    # Convert binary back to readable message
                    decoded_message = binary_to_message(binary_message)
                    
                    # Update chat with decoded message
                    update_chat(f"{nickname}: {decoded_message}")

                else:
                    # Show a message when CRC check fails
                    update_chat(f"CRC error in message from {nickname}")

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