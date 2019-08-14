import re

def get_host(headers):
    host = re.search(b'Host: (.*)\r', headers)
    if host:
        host = host.group(1).decode('utf-8')
        return host

    return None

def parse(data, thread, origin):
    if origin == 'client':
        host = get_host(data)
        if host:
            print('[{}] Request from client to {}'.format(thread.name, host))
    
    elif origin == 'server':
        pass