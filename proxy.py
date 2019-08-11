import os
import socket
import threading
from tqdm import tqdm
from importlib import reload
import parser
import argparse

p = argparse.ArgumentParser(description='HTTP proxy written in python')
p.add_argument('--debug', action='store_true')
args = p.parse_args()


PROXY_HOST = "newsite.cih.edu.mx"
PROXY_PORT = 80

BIND_ADDR = "0.0.0.0"
BIND_PORT = 80

class client_conn(threading.Thread):
    """Manages incoming connections"""
    def __init__(self, conn, info):
        threading.Thread.__init__(self)
        self.info = info
        self.server = None
        self.client = conn
        (self.ip, self.port) = self.info

    def run(self):
        while True:
            data = self.client.recv(1024)
            reload(parser)
            parser.parse(data, self, 'client')
            self.server.sendall(data)

class server_conn(threading.Thread):
    """Manages outgoing connections"""
    def __init__(self, conn, info):
        threading.Thread.__init__(self)
        self.info = info
        self.client = None
        self.server = conn
        (self.ip, self.port) = self.info
    
    def run(self):
        while True:
            data = self.server.recv(1024)
            if not data: break
            reload(parser)
            parser.parse(data, self.info, 'server')
            self.client.sendall(data)


client_sock = socket.socket()
client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_sock.bind((BIND_ADDR, BIND_PORT))

key = 0
threads = []

try:
    while True:

        for p in threads:
            for t in p:
                if not t.is_alive():
                    print('{} pipe is closed. terminating.'.format(t.name))
                    t.join()

        client_sock.listen(4)
        print('Listening for new connections...')
        (client, client_info) = client_sock.accept()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((PROXY_HOST, PROXY_PORT))
        
        # Start client thread with connection instance
        client_thread = client_conn(client, client_info)
        client_thread.name = "client[%d]" % key

        # Start server thread with connection instance
        server_thread = server_conn(server, (PROXY_HOST, PROXY_PORT))
        server_thread.name = "server[%d]" % key

        # Exchange connection info
        client_thread.server = server_thread.server
        server_thread.client = client_thread.client
        
        print("[proxy] new connection! ({}:{} <-> {} <-> {}:{})".format(client_info[0], client_info[1], "proxy[%d]" % key, PROXY_HOST, PROXY_PORT))

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

