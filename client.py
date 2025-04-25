import socket
import sys

def client(serverIP, serverPort):
    try:
        client_socket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creates socket
        client_socket.connect((serverIP, serverPort))
        print(f"Connected to server at {serverIP}:{serverPort}")          #validation message

        while True:
            message =input("Enter message to send to the server (or type 'exit' to quit): ")       #user input message

            if message.lower() =='exit':       #exit to close program
                break

            client_socket.sendall(message.encode('utf-8'))          #sends message

            response =client_socket.recv(1024).decode('utf-8')     #receives message
            print("Server response:", response)                     #server reply beginning message
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()           #closes socket

if __name__ =="__main__":
    serverIP =input("Enter the server IP address: ")              #enter server IP (public whatsmyIP)
    serverPort =int(input("Enter the server port number: "))      #port number for router rules
    client(serverIP, serverPort)