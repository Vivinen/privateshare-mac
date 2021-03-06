import PySimpleGUI as sg
import socket
import sys
import os
import time
from _thread import *
import threading

def threaded(srv_sock, port_number):
    """ 
    Enclose the following two lines in a try-except block to catch
    exceptions related to already bound ports, invalid/missing
    command-line arguments, port number out of range, etc.
    """
    try:
        """
        Register the socket with the OS kernel so that commands sent
        to the user-defined port number are delivered to this program.
        """
        srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv_sock.bind(("0.0.0.0", int(port_number)))

        # Report success post-binding
        print("Server up and running: 0.0.0.0 " + str(port_number) + " Port")
        print("Waiting for connection")

        # Initialize connection queue
        srv_sock.listen(5)
    except Exception as e:
        # Print the exception message
        print(e)
        # Close the server socket as well to release its resources back to the OS
        srv_sock.close()
        return

    running = True

    while running:

        """
        Surround the following code in a try-except block to account for
        socket errors as well as errors related to user input.
        """
        try:
            """
            Dequeue a connection request from the queue created by listen() earlier.
            If no such request is in the queue yet, this will block until one comes
            in. Returns a new socket to use to communicate with the connected client
            plus the client-side socket's address (IP and port number).
            """
            cli_sock,cli_adr = srv_sock.accept()
            print("Connected with" + str(cli_adr))

            # Receive the initial request from client
            request = cli_sock.recv(32)
            commands = request.decode('utf-8').split(',')

            # Handling of put request, sever side
            if (commands[0] == "put"):
                print("Put request received")
                directory = os.listdir()

                # Make sure the file is not a reupload, if yes then notify the client to continue
                if(not commands[1] in directory):
                    cli_sock.send("pass".encode('utf-8'))

                    # Try opening the file with exclusive creation binary mode
                    try:
                        f = open(commands[1],'xb')
                    except FileExistsError:
                        print("This file already exists")
                    data = cli_sock.recv(33554432)

                    # Begin receiving the upload
                    while(data):
                        print("Receiving...")
                        f.write(data)
                        data = cli_sock.recv(33554432)
                    f.close()
                    print("Done Receiving")
                    cli_sock.close()
                
                # If file is a reupload, notify the client and reject the file
                else:
                    cli_sock.send("cancel".encode('utf-8'))
                    time.sleep(1)
                    print("The server rejected the file. Filename already taken")
                    cli_sock.close()

            # Handling of get request, server side
            elif(commands[0] == "get"):
                print("Get request received")
                directory = os.listdir()

                # Make sure the file is in the servers directory, if yes then continue accordingly
                if(commands[1] in directory):
                    cli_sock.send("pass".encode('utf-8'))
                    f = open(commands[1],'rb')
                    print("Sending file to client")
                    data = f.read(33554432)
                    while(data):
                        print("Sending...")
                        cli_sock.send(data)
                        data = f.read(33554432)
                    f.close()
                    print("Finished sending file to client")
                    cli_sock.shutdown(socket.SHUT_WR)
                
                # Notify client that the file does not exist on the server and close connection
                else:
                    cli_sock.send("cancel".encode('utf-8'))
                    time.sleep(1)
                    print("The server does not have the file client is attempting to download")
                    cli_sock.close()

            # Handing of list request, server side
            elif(commands[0] == "list"):
                print("List request received")
                directory = os.listdir()
                directory_str = ""
                
                print("Sending list of File Directory...")

                for file in directory:	
                    add = file + ", "		
                    directory_str += add

                cli_sock.send(directory_str.encode('utf-8'))
                print("Finished sending directory")
                cli_sock.close()

            else:
                print("The connection encountered an error. Client must try again...")
        
        finally:
            """
            If an error occurs or the client closes the connection, call close() on the
            connected socket to release the resources allocated to it by the OS.
            """
            print("The connection has been closed")
            if 'cli_sock' in globals():
                cli_sock.close()
            return

    # Close the server socket as well to release its resources back to the OS
    srv_sock.close()

listen_lock = threading.Lock()

def Main():
    # Create server socket
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sg.theme('DarkAmber')   # Add a touch of color
    # All the stuff inside your window.
    layout = [  [sg.Text('Welcome to the privateshare server!')],
                [sg.Text('Server runs for 5 minutes at a time unless in current operation')],
                [sg.Text('Please note that the GUI will appear unresponsive during operations')],
                [sg.Text('Please enter the Port Number you wish to bind to:'), sg.InputText()],
                [sg.Output(size=(50,10), key='-OUTPUT-')],
                [sg.Button('Run Server'), sg.Button('Close Server')] ]

    # Create the Window
    window = sg.Window('privateshare server', layout)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if values[0]:
            port_number = int(values[0])
            if event in ('Run Server'):
                listen_lock.acquire()
                start_new_thread(threaded,(srv_sock, port_number,))
            window.refresh()
        else:
            print("Please enter a valid port number")
        
        if event in (None, 'Close Server'):   # if user closes window or clicks cancel
            break

        # Close the server socket as well to release its resources back to the OS
    window.close()

if __name__ == '__main__':
    Main()