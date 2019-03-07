import argparse
import random
import socket
import threading
import time
import pickle

MAX_CLIENTS = 5
list_of_clients = []
PORT = 5000
myLocation = (-1, -1)
peers_locations = {}


def main():
    global list_of_clients
    global PORT
    global myLocation
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("do_what", choices=['run'])
    args = parser.parse_args()

    if args.do_what == "run":
        ip_address, port, server = start_connection(args)
        PORT = port
        # check connection if established with server
        message = server.recv(2048)
        print("Server response: " + message.decode())
        server.send("handshake".encode('utf-8'))
        if args.verbose:
            print("connection successfully established with server\n")

        time.sleep(2)
        count = 0
        while True:
            sleep_time = int(random.uniform(2, 10))
            try:

                if count % 2 == 0:
                    request = "ping"
                    send_request(request, server)
                    time.sleep(2)
                    request = "location"
                    location = send_request(request, server)
                    myLocation = location
                    count += 1
                else:
                    request = "client_list"
                    server.send(request.encode('utf-8'))
                    message = server.recv(2048)
                    list_of_clients = pickle.loads(message)
                    count +=1

            except Exception as e:
                print("Server not reachable")
                print(e)
                print("\n")
                """ Start a peer to peer communication with the available clients"""
                server.close()
                p2p()

            time.sleep(sleep_time)


def start_connection(args):
    print("Client connecting to server ...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = str(args.ip)
    port = int(args.port)
    server.connect((ip_address, port))
    print("Connected at port: %d - ip %s\n" % (port, ip_address))
    return ip_address, port, server


def send_request(request, server):
    print("Client request -> " + request)
    server.send(request.encode("utf-8"))
    message = server.recv(2048)
    print("Server response => " + message.decode())
    print()
    return message


def get_host_name_ip():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        return host_ip
    except Exception as e:
        print("Unable to get Hostname and IP")
        print(e)


def p2p():
    print("Setting up peer - peer connection ...")
    host_ip = get_host_name_ip()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create Datagram Socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # make socket reusable
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # allow incoming broadcast
    s.setblocking(False) # Set socket to non-blocking mode

    try:
        s.bind(('', PORT)) # Accept Connections on port
        print("Accepting connections on port " + str(PORT))
    except Exception as e:
        print(e)
        pass

    while True:
        sleep_time = int(random.uniform(2, 10))
        try:
            message, address = s.recvfrom(2024)
            if message:
                print("From: " + str(address) + " -> ")
                print(pickle.loads(message))
                time.sleep(sleep_time)
                add_to_dic(str(address), pickle.loads(message))
                print(peers_locations)
        except Exception as e:
            print("No reachable peer ...")
            time.sleep(sleep_time)

        for c in list_of_clients:
            address = (c[0], PORT)
            if host_ip != address[0]:
                msg = str(myLocation)
                s.sendto(pickle.dumps(msg), address)


def add_to_dic(address, location):
    if address not in peers_locations:
        peers_locations[address] = location


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    main()
