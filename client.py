#!/user/bin/env python
# -*- encoding:utf-8 -*-
import socket
import requests


def main():
    '''
    addr = ("127.0.0.1", 8888)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect(addr)
    s.send("test" * 100)
    s.close()
    '''
    params = {'key1': 'value1', 'key2': 'value2'}
    r = requests.post("http://127.0.0.1:8888/testuri?p1=v1&p2=v2", data=payload)
    print r.text

if __name__ == '__main__':
    main()
