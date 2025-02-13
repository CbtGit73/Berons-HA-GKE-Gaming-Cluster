import socket

server_ip = "34.32.70.90" # Change to IP address assigned to pod
server_port = 7972 # Change to the port of the server you want to test
message = "Hello from the otherside"

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send the message
    print(f"Sending: '{message}' to {server_ip}:{server_port}")
    sock.sendto(message.encode(), (server_ip, server_port))

    sock.settimeout(5)  # 5 seconds timeout
    try:
        response, addr = sock.recvfrom(1024)  # Buffer size of 1024 bytes
        print(f"Received from {addr}: {response.decode()}")
    except socket.timeout:
        print("No response received (you might be ugly)")

finally:
    sock.close()
    print("Connection closed. Have a blessed day.")

