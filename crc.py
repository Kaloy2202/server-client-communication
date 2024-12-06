import random

# CRC Functions
def append_crc(message):
    # Generator polynomial in binary (x^4 + x + 1)
    generator = "10011"
    n = len(generator) - 1
    
    # Append n zero bits to the message
    message_binary = ''.join(format(ord(char), '08b') for char in message)
    padded_message = message_binary + '0' * n

    # Modulo 2 division
    remainder = modulo2_division(padded_message, generator)
    transmitted_message = padded_message[:len(message_binary)] + remainder

    # Simulate random bit flip with 5% probability
    if random.random() < 0.05:
        bit_to_flip = random.randint(0, len(transmitted_message) - 1)
        transmitted_message = (
            transmitted_message[:bit_to_flip] +
            ('1' if transmitted_message[bit_to_flip] == '0' else '0') +
            transmitted_message[bit_to_flip + 1:]
        )
        print(f"Bit flipped at position {bit_to_flip}!")

    return transmitted_message

def validate_crc(received_message):
    generator = "10011"
    n = len(generator) - 1
    
    # Extract original message and CRC
    original_message_binary = received_message[:-n]
    remainder = modulo2_division(received_message, generator)

    # Convert binary back to string
    original_message = ''.join(
        chr(int(original_message_binary[i:i + 8], 2)) for i in range(0, len(original_message_binary), 8)
    )

    # If remainder is all zeros, CRC is valid
    is_valid = all(bit == '0' for bit in remainder)
    return is_valid, original_message

def modulo2_division(dividend, divisor):
    dividend = list(dividend)
    divisor = list(divisor)
    for i in range(len(dividend) - len(divisor) + 1):
        if dividend[i] == '1':  # Perform XOR only when bit is 1
            for j in range(len(divisor)):
                dividend[i + j] = '1' if dividend[i + j] != divisor[j] else '0'
    return ''.join(dividend[-(len(divisor) - 1):])

# Debug CRC Functions
if __name__ == "__main__":
    test_message = "Hello"
    print(f"Original Message: {test_message}")
    
    # Append CRC
    transmitted = append_crc(test_message)
    print(f"Transmitted Message: {transmitted}")
    
    # Validate CRC
    is_valid, original_message = validate_crc(transmitted)
    print(f"CRC Valid: {is_valid}")
    print(f"Original Message Extracted: {original_message}")

    dividend = "11010011101100"  # Example binary message
    divisor = "1011"  # Generator polynomial
    remainder = modulo2_division(dividend, divisor)
    print(f"Dividend: {dividend}")
    print(f"Divisor: {divisor}")
    print(f"Remainder: {remainder}")

    test_message = "Hello"
    transmitted = append_crc(test_message)
    print(f"Transmitted Message: {transmitted}")

    # Introduce an error
    tampered_message = transmitted[:10] + ('1' if transmitted[10] == '0' else '0') + transmitted[11:]
    is_valid, original_message = validate_crc(tampered_message)
    print(f"Tampered Message: {tampered_message}")
    print(f"Is CRC Valid: {is_valid}")
    print(f"Original Message: {original_message}")


    is_valid, original_message = validate_crc(transmitted)
    print(f"Is CRC Valid: {is_valid}")
    print(f"Original Message: {original_message}")


