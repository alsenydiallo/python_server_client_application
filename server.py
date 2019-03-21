import argparse
import socket
import select
import sys
import threading
from _thread import *
from coverage_greedy_enhanced import *
import pickle


MAX_CLIENTS = 5
list_of_clients = []
server_tag_location_list = []
log_file_path = "log.server.txt"
debug = False

"""The following function simply removes the object 
from the list that was created at the beginning of  
the program"""


def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)


def handle_request(clientsocket, addr):
    while True:
        try:
            message = clientsocket.recv(2048)
            message = message.decode()
            thread_id = str(threading.currentThread().getName())
            print("%s: < %s > %s" % (thread_id, addr[0], message))

            if message == "handshake":
                print("handshake received from client " + thread_id + "/" + addr[0])
            elif message == "ping":
                clientsocket.send('awake !'.encode('utf-8'))
            elif message == "location":
                print("server computing location for " + thread_id + "/" + addr[0])
                signal_received_at = suggest_point()
                location = predict_location(server_tag_location_list, signal_received_at)
                print("signal received at <" + signal_received_at.toString() + ">, computed location <" + location.toString() + ">")
                clientsocket.send(location.toString().encode('utf-8'))
                # clientsocket.send("(0,0)".encode('utf-8'))
                distance = signal_received_at.distance(location)
                log_to_file(distance)

            elif message == "client_list":
                client = []
                for c in list_of_clients:
                    client.append(c.getpeername())
                m = pickle.dumps(client)
                clientsocket.send(m)
            else:
                """message may have no content if the connection 
                is broken, in this case we remove the connection"""
                remove(clientsocket)
                print("client disconnected")
                # threading.currentThread().setDaemon(True)
                exit_thread()

        except Exception as e:
            print(e)
            exit_thread()


def get_location_list():
    print_list(server_tag_location_list)
    return server_tag_location_list


def log_to_file(distance):
    if distance >= 0:
        fd = open(log_file_path, "a+")
        fd.write(str(distance)+"\n")
        fd.close()


def main():
    global debug
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("do_what", choices=['run'])
    args = parser.parse_args()

    if args.do_what == 'run':
        print("Starting server ...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ip_address = str(args.ip)
        port = int(args.port)

        if args.verbose:
            debug = args.verbose

        if debug:
            print("Server loading tag map ...")

        try:
            global server_tag_location_list
            tag_location_grid, server_tag_location_list = read_grid_from_file("20x20_50k_3tx.txt")
            tx = getTX()
            grid_stat(server_tag_location_list, tx)
            server.bind((ip_address, port))
            server.listen(MAX_CLIENTS)
            print("Server up successfully !")
            print("listening on port: %d - ip %s\n" % (port, ip_address))

            if debug:
                print_grid_2(tag_location_grid, server_tag_location_list)
                print_list(server_tag_location_list)
        except Exception as e:
            print(e)

        while True:
            clientsocket, addr = server.accept()
            list_of_clients.append(clientsocket)
            print("\n" + addr[0] + " connected\n")
            clientsocket.send('handshake '.encode('utf-8'))
            start_new_thread(handle_request, (clientsocket, addr))
            if args.verbose: print(list_of_clients)


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    main()
