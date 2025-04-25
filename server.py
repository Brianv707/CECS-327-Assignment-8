import socket
import sys

def server(host, port):
    # Create a TCP/IP socket
    server_socket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)        #creates socket
    server_socket.bind((host, port))                                        #binds host and port together
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}...")                          #server listening confirmation message

    while True:
        client_socket, client_address = server_socket.accept()              #waits for connection
        print(f"Connection established with {client_address}")              #connection confirmation message

        while True:
            data =client_socket.recv(1024)      #receives message
            if not data:                        #if message isn't good break
                break
            
            print("Received message: ",data.decode('utf-8'))        #received message confirmation

            response =data.decode('utf-8').upper()                  #sends message back in all uppercase
            client_socket.sendall(response.encode('utf-8'))         #sends message
        
        client_socket.close()                                       #closes socket
        print(f"Connection closed with {client_address}")           #connection closed confirmation message

if __name__=="__main__":
    host =input("Enter the server IP address: ")         #prompts user to enter IP server is hosted on
    port =int(input("Enter the port number: (I used 12345)"))                       #prompts user to enter port # to connect to
    try:
        server(host, port)
    except Exception as e:
        print(f"Error starting server: {e}")