import argparse
import random
import socket
import threading
import time
import pickle
import re
from coverage_greedy_enhanced import *
from point import *

MAX_CLIENTS = 5
list_of_clients = []
PORT = 5000
myLocation = Point(-1,-1,0)
peers_locations = {}
Tx = 5
debug = False
log_file_path = "log.client.txt"
peer_log_file_path = "log.peer.txt"


def main():
    global list_of_clients
    global PORT
    global myLocation
    global debug
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
            debug = args.verbose
            print("connection successfully established with server\n")

        if debug:
            time.sleep(2)

        count = 0
        while True:
            if debug: sleep_time = int(random.uniform(2, 10))
            try:

                if count % 2 == 0:
                    request = "ping"
                    send_request(request, server)
                    if debug: time.sleep(2)
                    request = "location"

                    start = time.time()
                    location = send_request(request, server)
                    stop = time.time()
                    diff = stop - start
                    log_to_file(str(diff)+"\n")
                    myLocation = location
                    count += 1
                else:
                    request = "client_list"
                    server.send(request.encode('utf-8'))
                    message = server.recv(2048)
                    list_of_clients = pickle.loads(message)
                    count += 1

            except Exception as e:
                print("Server not reachable <disconnected>")
                print(e)
                print("\n")
                """ Start a peer to peer communication with the available clients"""
                server.close()
                p2p()

            if debug: time.sleep(sleep_time)


def start_connection(args):
    print("Client connecting to server ...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = str(args.ip)
    port = int(args.port)
    try:
        server.connect((ip_address, port))
        print("Connected at port: %d - ip %s\n" % (port, ip_address))
    except Exception as e:
        print("Server not reachable <not up and running>")
        print(e)
        print("\n")
        """ Start a peer to peer communication with the available client"""
        p2p()

    return ip_address, port, server


def send_request(request, server):
    print("Client request -> " + request)
    server.send(request.encode("utf-8"))
    message = server.recv(2048)
    print("Server response => " + message.decode())
    print()

    if request == "location":
        message = message.decode()
        return extract_location(message)

    return message


def extract_location(message):
    temp = message
    int_list = [float(s) for s in re.findall(r'-?\d+\.?\d*', temp)]
    location = Point(int_list[0], int_list[1], 0)
    return location


def get_host_name_ip():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        return host_ip
    except Exception as e:
        print("Unable to get Hostname and IP")
        print(e)


def p2p():
    global debug
    global myLocation
    print("Setting up peer - peer connection ...")
    host_ip = get_host_name_ip()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Datagram Socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # make socket reusable
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # allow incoming broadcast
    s.setblocking(False)  # Set socket to non-blocking mode

    try:
        s.bind(('', PORT))  # Accept Connections on port
        print("Accepting connections on port " + str(PORT))
        # mimic that the device has entered the covered zone and is moving

        print("My location")
        myLocation.display()
        print("\n")
        if myLocation.equal(Point(-1,-1,0)) == 0:
            print("Initializing mylocation")
            myLocation = suggest_point()

    except Exception as e:
        print(e)
        pass

    while True:

        for c in list_of_clients:
            address = (c[0], PORT)
            if host_ip != address[0]:
                msg = str(myLocation)
                s.sendto(pickle.dumps(msg), address)

        if debug: sleep_time = int(random.uniform(2, 4))

        try:
            message, address = s.recvfrom(2024)
            if message:
                print("Received coord from: " + str(address))
                # print(pickle.loads(message))
                add_to_dic(str(address), pickle.loads(message))
                display_dic()
                if debug: time.sleep(sleep_time)
                # compute new location coordinate
                # print("my coord - " + myLocation.toString())
                # location = predict_location(peers_locations_list(), myLocation)
                # print("My new coord - " + location.toString())
        except Exception as e:
            print("No reachable peer ...")
            print(e)
            if debug: time.sleep(sleep_time)


def add_to_dic(address, location):
    loc = extract_location(location)
    d = loc.distance(myLocation)
    if d >= 0:
        peers_locations[address] = loc


def peers_locations_list():
    locations = ()
    for peer in list_of_clients:
        locations.append(list_of_clients[peer])
    return locations


def display_dic():
    print("\n-------------------------------------")
    print("Near by peer - most recent data")
    for peer in peers_locations:
        loc = peers_locations[peer]
        print(str(peer) + "-> " + loc.toString())
    print("-------------------------------------")
    print("\n")


def log_to_file(latency):
    fd = open(log_file_path, "a+")
    fd.write(latency)
    fd.close()

# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    main()
