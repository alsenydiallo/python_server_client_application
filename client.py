import argparse
import random
import socket
import threading
import time
from _thread import start_new_thread

from coverage_greedy_enhanced import suggest_point, predict_location, print_list, read_grid_from_file
from server import get_location_list
from server import server_tag_location_list

MAX_CLIENTS = 5
n, m = 10, 10
client_tag_location_list = server_tag_location_list


def main():
    global client_tag_location_list
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("do_what", choices=['run'])
    args = parser.parse_args()

    if args.do_what == "run":
        IP_address, Port, server = start_connection(args)

        # check connection if established with server
        message = server.recv(2048)
        print("Server response: " + message.decode())
        if args.verbose:
            print("connection successfully established with server\n")

        _, client_tag_location_list = read_grid_from_file("test.out")

        time.sleep(2)
        while True:
            sleep_time = int(random.uniform(2, 10))
            try:
                request = "ping"
                send_request(request, server)
                time.sleep(2)
                request = "location"
                send_request(request, server)
            except Exception as e:
                print("Server not reachable")
                print(e)
                print("\n")
                time.sleep(2)

                try:
                    while True:
                        print("Client establishing new connection...")
                        server.close()

                        # new connection
                        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        server.bind((IP_address, Port))
                        server.listen(MAX_CLIENTS)

                        while True:
                            clientsocket, addr = server.accept()
                            print("\n" + addr[0] + " connected\n")
                            clientsocket.send('handshake '.encode('utf-8'))
                            start_new_thread(handle_request, (clientsocket, addr))

                except Exception as e:
                    print(e)
                    IP_address, Port, server = start_connection(args)
                    message = server.recv(2048)
                    print("Server response: " + message.decode())
                    if args.verbose:
                        print("connection successfully established with server\n")

                    time.sleep(2)
                    while True:
                        sleep_time = int(random.uniform(2, 10))
                        try:
                            request = "ping"
                            send_request(request, server)
                            time.sleep(2)
                            request = "location"
                            send_request(request, server)
                        except Exception as e:
                            print("Server not reachable")
                            print(e)
                            print("\n")
                            time.sleep(2)

                            print("break")
                            break

                        time.sleep(sleep_time)
                    continue
            time.sleep(sleep_time)


def start_connection(args):
    print("Client starting ...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    IP_address = str(args.ip)
    Port = int(args.port)
    server.connect((IP_address, Port))
    print("Client running ...")
    print("Connected at port: %d - ip %s\n" % (Port, IP_address))
    return IP_address, Port, server


def send_request(request, server):
    print("Client request -> " + request)
    server.send(request.encode("utf-8"))
    message = server.recv(2048)
    message = message.decode()
    print("Server response: " + message)
    print()


def handle_request(clientsocket, addr):
    while True:
        try:
            message = clientsocket.recv(2048)
            message = message.decode()
            thread_id = str(threading.currentThread().getName())
            print("%s: < %s > %s" % (thread_id, addr[0], message))
            if message == "ping":
                clientsocket.send('awake !'.encode('utf-8'))

            elif message == "location":
                print("server computing location for " + thread_id + "/" + addr[0])
                signal_received_at = suggest_point()
                location = predict_location(client_tag_location_list, signal_received_at)
                print("signal received at <" + signal_received_at.toString() + ">, computed location <" + location.toString() + ">")
                clientsocket.send(location.toString().encode('utf-8'))

        except Exception as e:
            print(e)
            continue


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    main()
