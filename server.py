#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sys
import core
import socket
import os
import multiprocessing
import logging
import protocol


class Task(core.TaskInterface):

    def init(self):
        self.http = protocol.Http()
        self.__init_notfound()
        self.uri_map = {
            '/wikiabs': self.wikiabs,
        }

    def on_receive(self, fd):
        data = self.fd_info(fd).received_data
        self.http.parse(data)
        self.fd_info(fd).append(self.http.left_data)
        func = self.uri_map.get(self.http.uri)
        if func is None:
            self.fd_info(fd).send(self.__not_found)
        else:
            func(fd)

    def on_send(self, fd):
        self.fd_info(fd).clean_fd()

    def __init_notfound(self):
        content = "404 NOT FOUND"
        headers = {
            'Content-Type': 'text/html;charset=utf-8',
            'Connection': 'keep-alive',
        }
        self.__not_found = self.http.format(headers, content)

    def wikiabs(self, fd):
        # reply
        content = "yoyochecknow 中文"
        headers = {
            'Content-Type': 'text/html;charset=utf-8',
            'Connection': 'keep-alive',
        }

        send_data = self.http.format(headers, content)
        self.fd_info(fd).send(send_data)



def init_logger(path, filename):
    '''初始化日志
    '''
    fmt = '%(levelname)s %(asctime)s %(filename)s|%(lineno)d %(message)s'
    formatter = logging.Formatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        os.mkdir(path)
    except OSError:
        pass
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

    '''
    # fork 多个进程
    for i in xrange(process_num):
        new_pid = os.fork()
        if new_pid == 0:
            svr = core.Loop(listen_fd, timeout, 10, Task)
            svr.run()
    '''
    svr = core.Loop(listen_fd, timeout, 10, Task)
    svr.run()


if __name__ == '__main__':
    main()
