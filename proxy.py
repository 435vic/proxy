import os
import socket
import threading
from tqdm import tqdm

PROXY_HOST = "newsite.cih.edu.mx"
PROXY_PORT = "80"

BIND_ADDR = "0.0.0.0"
BIND_PORT = 1337

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
            if not data: break
            print("[{} <- {}:{}] received data:\n{}".format(self.name, self.ip, self.port, data.decode('utf-8')))
            self.server.send(data)

class server_conn(threading.Thread):
    """Manages outgoing connections"""
    def __init__(self, conn, info):
        threading.Thread.__init__()
        self.client = None
        self.server = conn
    
    def run():
        pass



client_sock = socket.socket()
client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_sock.bind((BIND_ADDR, BIND_PORT))

key = 0
threads = []

try:
    while True:
        sock.listen(4)
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
        for t in tqdm(threads):
            t.join()
    print('exiting...')
    exit()

