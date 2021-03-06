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
myLocation = Point(0,0,0)
peers_locations = {}
deviceTx = 5
debug = False
latency_fpath = "log.client.latency.txt"
correctness_fpath = "log.client.correct.txt"
n = 10
m = 10

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
                    log_to_file(latency_fpath, str(diff))
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

        print("Current location " + myLocation.toString())
        print("\n")

    except Exception as e:
        print(e)
        pass

    count = 0
    while True:

        for c in list_of_clients:
            address = (c[0], PORT)
            if str(host_ip) != str(address[0]):
                msg = myLocation.toString()
                s.sendto(pickle.dumps(msg), address)

        if debug: sleep_time = int(random.uniform(2, 4))

        try:
            message, address = s.recvfrom(2024)
            if message:
                if host_ip != address:
                    # print("Received coord from: " + str(address) + " -> " + pickle.loads(message))
                    add_to_dic(str(address), pickle.loads(message))
                    display_dic()
                    if debug:time.sleep(sleep_time)

                    if debug:print("Current coord - " + myLocation.toString())
                    location_list = peers_locations_list()

                    # move location of device
                    if count % 2 == 0:
                        myLocation = move_x(myLocation, 2)
                        count +=1
                    elif count % 2 == 1:
                        myLocation = move_y(myLocation, 2)
                        count +=1

                    location = compute_client_location(location_list, myLocation, deviceTx)
                    if debug:print("New computed coord - " + location.toString())
                    diff = myLocation.distance(location)
                    log_to_file(correctness_fpath, str(diff))
                    myLocation = location
        except Exception as e:
            print("No reachable peer ...")
            print(e)
            if debug: time.sleep(sleep_time)


def move_x(location, seed):
    if location.x-seed < n:
        location.x += seed
    else: location.x -= seed
    return location


def move_y(location, seed):
    if location.y - seed < m:
        location.y += seed
    else:
        location.y -= seed
    return location


def compute_client_location(tag_list, signal_received_at, deviceTx):
    location = Point(0, 0, 1)
    list_len = len(tag_list)

    try:
        if list_len == 1:
            location = tag_list[0]
        elif list_len == 2:
            tag_heap = heap_of_tags(tag_list, signal_received_at)
            k1, tag1 = heapq.heappop(tag_heap)
            k2, tag2 = heapq.heappop(tag_heap)
            location = score_func_case_2_helper(signal_received_at, tag1, tag2, deviceTx)
        elif list_len >= 3:
            tag_heap = heap_of_tags(tag_list, signal_received_at)
            k1, tag1 = heapq.heappop(tag_heap)
            k2, tag2 = heapq.heappop(tag_heap)
            k3, tag3 = heapq.heappop(tag_heap)
            location = compute_matrix(tag1, tag2, tag3, signal_received_at)
    except Exception as e:
        print("Error in compute location")
        print(e)

    if location.equal(Point(-1,-1,0)) == 0:
        location = suggest_location()

    return location


def suggest_location():
    x = int(random.uniform(0, n))
    y = int(random.uniform(0, m))
    return Point(x, y, 1)


def add_to_dic(address, location):
    loc = extract_location(location)
    d = loc.distance(myLocation)
    if 0 <= d <= (deviceTx * 2):
        peers_locations[address] = loc
    return loc


def peers_locations_list():
    locations = []
    for peer in peers_locations:
        locations.append(peers_locations[peer])

    return locations


def display_dic():
    print("\n-------------------------------------")
    print("Near by peer - most recent data")
    for peer in peers_locations:
        loc = peers_locations[peer]
        print(str(peer) + "-> " + loc.toString())
    print("-------------------------------------")
    print("\n")


def log_to_file(log_file_path, data):
    buffer = str(str(data) + "\n")
    fd = open(log_file_path, "a+")
    fd.write(buffer)
    fd.close()


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    main()
