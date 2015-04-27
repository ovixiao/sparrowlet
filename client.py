import socket
import protocol.sushi


addr = ("127.0.0.1", 8888)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(addr)

s.send("hello")
s.send("world")

s.close()
