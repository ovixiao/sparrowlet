import socket
import server
import sys
import tasks


def listen_socket(port):
    try:
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_fd.bind(('', port))
        listen_fd.listen(1024)
        listen_fd.setblocking(0)
    except socket.error as e:
        return None

    return listen_fd


def main():
    reload(sys)
    sys.setdefaultencoding("utf8")

    port = 8888
    listen_fd = listen_socket(port)
    task_manager = tasks.Manager()

    if listen_fd:
        timeout = 10
        svr = server.Server(listen_fd, timeout, task_manager)
        svr.epoll_loop()


if __name__ == '__main__':
    main()
