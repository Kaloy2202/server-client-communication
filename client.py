import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
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

# Client Configuration
HOST = '192.168.68.102'  # Should match the server's IP
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
        try:
            message = message_field.get()
            if message:
                print(f"Original Message: {message}")
                crc_message = append_crc(message)
                print(f"CRC Encoded Message: {crc_message}")

                # Display the sent message and CRC status
                update_chat(f"Sent: {message}")
                update_chat(f"CRC Encoded: {crc_message}")
                client_socket.send(crc_message.encode('utf-8'))
        except Exception as e:
            print(f"Error in send_message: {e}")


    # Send button for client GUI
    send_button = tk.Button(root, text="Send", command=send_message)
    send_button.pack(pady=5)

    # Listen for incoming messages
    
    # Receiving messages with CRC validation
    # Function to receive messages with CRC validation
    def receive_messages():
        while True:
            try:
                received_message = client_socket.recv(1024).decode('utf-8')
                if not received_message:
                    print("[DEBUG] Server closed the connection.")
                    break

                # Validate CRC and display status
                is_valid, original_message = validate_crc(received_message)
                if is_valid:
                    update_chat(f"Received (Valid): {original_message}")
                else:
                    update_chat(f"Received (Invalid): {received_message}")
            except Exception as e:
                print(f"[ERROR] receive_messages: {e}")
                break
        client_socket.close()



    # Start the receive thread
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()

    # Handle window close
    def on_closing():
        try:
            leave_chat()
        except Exception as e:
            print(f"Error during closing: {e}")
    
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Trigger leave_chat when window closes
    root.mainloop()
