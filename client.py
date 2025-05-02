import socket
import sys


queries={
    "1": "What is the average moisture inside my kitchen fridge in the past three hours?",          #dictionary, mapping query number to actual query
    "2": "What is the average water consumption per cycle in my smart dishwasher?",
    "3": "Which device consumed more electricity among my three IoT devices (two refrigerators and a dishwasher)?"
}

def client(serverIP, serverPort):
    try:
        client_socket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creates socket
        client_socket.connect((serverIP, serverPort))
        print(f"Connected to server at {serverIP}:{serverPort}")          #validation message

        while True:
            print("Please select a query:")
            for key, query in queries.items():
                print(f"{key}. {query}")
            print("Type 'exit' to quit")
            
            message=input("\nEnter your query number (1-3): ")          #changes message to become query selection
            
            
            if message.lower() =='exit':       #exit to close program
                break
            
            if message not in queries:
                print("Sorry, this query cannot be processed. Please try one of the following:")
                for key, query in queries.items():
                    print(f"{key}. {query}")
                continue

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