import socket


addr = ("127.0.0.1", 8888)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect(addr)


s.send("test")

s.close()
