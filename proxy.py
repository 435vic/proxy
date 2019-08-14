import os
import socket
import threading
from tqdm import tqdm
from importlib import reload
import parser
import argparse
import re

p = argparse.ArgumentParser(description='HTTP proxy written in python')
p.add_argument('--debug', action='store_true')
args = p.parse_args()

# PROXY_HOST = "newsite.cih.edu.mx"
PROXY_PORT = 80

BIND_ADDR = "0.0.0.0"
BIND_PORT = 80

class client_conn(threading.Thread):
    """Manages incoming connections"""
    def __init__(self, conn, info):
        threading.Thread.__init__(self)
        self.info = info
        self.server = None
        self.destination = None
        self.client = conn
        self.terminated = False
        # if client uses same connection (thread) to contact different hosts,
        # we use this info to forward it to the appropieate host
        self.forward_info = None
        (self.host, self.port) = self.info

    def run(self):
        while True:
            data = self.client.recv(1024)
            if not data: break
            # If no host header is found then obviously it is intended for the same host
            if parser.get_host(data) and not self.destination == parser.get_host(data):
                print('[{}] request to host {} does not match server host {}'.format(self.name, parser.get_host(data), self.destination))
                # Give new host along with client socket to keep communication with client
                self.forward_info = (self.client, self.info, parser.get_host(data), data)
                break

            reload(parser)
            parser.parse(data, self, 'client')
            try:
                self.server.sendall(data)
            except BrokenPipeError:
                print('[{}] broken pipe :/'.format(self.name))
                break
        print('[{}] exiting...'.format(self.name))
        return

class server_conn(threading.Thread):
    """Manages outgoing connections"""
    def __init__(self, conn, info):
        threading.Thread.__init__(self)
        self.info = info
        self.client = None
        self.server = conn
        self.forward_info = None
        self.terminated = False
        (self.ip, self.port) = self.info
    
    def run(self):
        while True:
            try:
                data = self.server.recv(1024)
            except ConnectionResetError:
                print('[{}] connection reset :/'.format(self.name))
                return

            if not data: break
            reload(parser)
            parser.parse(data, self.info, 'server')
            try:
                self.client.sendall(data)
            except BrokenPipeError:
                print('[{}] broken pipe :/'.format(self.name))
                break

key = 0
threads = []

class Watchdog(threading.Thread):
    """ Constantly checks state of threads """
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        while True:
            for p in threads:
                for t in p:
                    if not t.terminated and not t.is_alive():
                        print('{} pipe is closed. terminating.'.format(t.name))
                        if t.forward_info:
                            # oops...
                            (client, client_info, destination, request) = t.forward_info
                            print('[proxy] Creating new connection from {}:{}'.format(client_info[0], client_info[1]))
                            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                            # Start client thread with connection instance
                            client_thread = client_conn(client, client_info)
                            key = int(re.search('\[(\d+)\]', t.name).group(1))
                            client_thread.name = "client[%d]" % key
                            
                            # Forward request to server
                            # Prev. thread died before sending it, since the socket
                            # provided to it was connected to a different host
                            server.connect((destination, PROXY_PORT))
                            server.sendall(request)

                            # Start server thread with connection instance
                            server_thread = server_conn(server, (destination, PROXY_PORT))
                            server_thread.name = "server[%d]" % key

                            # Exchange connection info
                            client_thread.server = server_thread.server
                            client_thread.destination = destination
                            server_thread.client = client_thread.client
                            
                            print("[proxy] new connection! ({}:{} <-> {} <-> {}:{})".format(client_info[0], client_info[1], "proxy[%d]" % key, destination, PROXY_PORT))

                            client_thread.start()
                            server_thread.start()
                            
                            threads.append((client_thread, server_thread))
                        
                        t.join()
                        t.terminated = True



client_sock = socket.socket()
client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_sock.bind((BIND_ADDR, BIND_PORT))

try:
    w = Watchdog()
    w.start()
    while True:
        client_sock.listen(4)
        print('Listening for new connections...')
        (client, client_info) = client_sock.accept()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Start client thread with connection instance
        client_thread = client_conn(client, client_info)
        client_thread.name = "client[%d]" % key
        
        # Read request header to find destination
        request = client.recv(1024)
        if request:
            destination = parser.get_host(request)
        
        print("[proxy] got destination for new connection: {}".format(destination))

        # Connect to destination with our new info and forward request
        # We have to do this manually as neither the client or the server threads are running yet
        server.connect((destination, PROXY_PORT))
        server.sendall(request)

        # Start server thread with connection instance
        server_thread = server_conn(server, (destination, PROXY_PORT))
        server_thread.name = "server[%d]" % key

        # Exchange connection info
        client_thread.server = server_thread.server
        client_thread.destination = destination
        server_thread.client = client_thread.client
        
        print("[proxy] new connection! ({}:{} <-> {} <-> {}:{})".format(client_info[0], client_info[1], "proxy[%d]" % key, destination, PROXY_PORT))

        client_thread.start()
        server_thread.start()
        
        threads.append((client_thread, server_thread))
        
        key += 1

except KeyboardInterrupt:
    print("\nKeyboard Interrupt (Ctrl-C was pressed)")
    if (threads):
        print("terminating threads...")
        for tu in tqdm(threads):
            tu[0].join()
            tu[1].join()
    
    print('exiting...')
    exit()

