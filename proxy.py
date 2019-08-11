import os
import socket
import threading
from tqdm import tqdm

class connInstance(threading.Thread):
    def __init__(self, conn, info):
        threading.Thread.__init__(self)
        self.info = info
        self.conn = conn
        (self.ip, self.port) = self.info
        print('[+] new connection from %s:%s' % self.info)
    def run(self):
        while True:
            data = self.conn.recv(1024)
            if not data: break
            print("[+] received data: %s" % data)
            self.conn.send(data)

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 1337))
threads = []

try:
    while True:
        sock.listen(4)
        print('Listening for new connections...')
        (conn, info) = sock.accept()
        thread = connInstance(conn, info)
        thread.start()
        threads.append(thread)

except KeyboardInterrupt:
    print("\nKeyboard Interrupt (Ctrl-C was pressed)")
    if (threads):
        print("terminating threads...")
        for t in tqdm(threads):
            t.join()
    print('exiting...')
    exit()

