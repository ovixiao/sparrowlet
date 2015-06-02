#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sys
import core
import socket
import os
import multiprocessing
import logging


class Task(core.TaskInterface):

    def on_receive(self, fd):
        self.fd_info(fd).send('hahaha')

    def on_send(self, fd):
        self.fd_info(fd).clean_fd()


def init_logger(path, filename):
    fmt = '%(levelname)s %(asctime)s %(filename)s|%(lineno)d %(message)s'
    formatter = logging.Formatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    os.mkdir(path)
    fh = logging.FileHandler("{}/{}".format(path, filename))
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def init_listen(port):
    '''初始化监听 socket

    参数:
        port: 监听端口
    '''
    listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_fd.bind(('', port))
    listen_fd.listen(10240)
    listen_fd.setblocking(0)

    return listen_fd


def main():
    reload(sys)
    sys.setdefaultencoding("utf8")


    port = 8888
    timeout = 10
    init_logger('log', 'sparrow.log')
    process_num = multiprocessing.cpu_count()
    listen_fd = init_listen(port)

    # fork 多个进程
    for i in xrange(process_num):
        new_pid = os.fork()
        if new_pid == 0:
            svr = core.Loop(listen_fd, timeout, 10, Task)
            svr.run()
    svr = core.Loop(listen_fd, timeout, 10, Task)
    svr.run()


if __name__ == '__main__':
    main()
