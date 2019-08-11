import re

def parse(data, thread, origin):
    if origin == 'client':
        host = re.search('Host: (.*)').group(1)
        print('[{}] Request from client to {}'.format(thread.name, host))