#!/user/bin/env python
# -*- encoding:utf-8 -*-
'''
基于 epoll 的 TCP 简单网络框架.
'''
import socket
import select
import time
import logging
from fd_manager import FdManager
from fd_info import FdInfo
from task_manager import TaskManager


class Loop(object):
    '''服务端循环对应的类
    包含了如下几种操作的服务端:
    1. 删除: remove
    2. 新建: new
    3. 发送数据: send
    4. 接受数据: receive
    '''

    def __init__(self, listen_fd, timeout, tasklet_num, task_class):
        '''初始化

        参数:
            listen_fd: 监听 socket
            port: 监听端口
            timeout: 超时时长
            tasklet_num: 微线程个数
        '''
        # 传入的参数
        self.timeout = timeout
        self.listen_fd = listen_fd
        #  响应的事件
        self.events = select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP
        # epoll 的文件描述子
        self.epoll_fd = None
        self.__init_epoll()
        # 文件描述子管理器
        self.fd_manager = FdManager(self.epoll_fd)
        # 任务管理器
        self.__task = task_class(self.fd_manager)
        self.task_manager = TaskManager(tasklet_num)
        # log
        self.logger = logging.getLogger()

    def __init_listen(self, port):
        '''初始化监听 socket

        参数:
            port: 监听端口
        '''
        self.listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_fd.setblocking(0)
        self.listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_fd.bind(('', port))
        self.listen_fd.listen(10240)

    def __init_epoll(self):
        '''初始化 epoll, 注册各种操作 event
        '''
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.listen_fd.fileno(), self.events)
        except select.error as e:
            self.logger.critical(str(e))
            self.epoll_fd = None

    def __event_new(self):
        ''' 创建一个新的 fd, 会进行如下操作:
        1. 接收监听 socket
        2. 创建新的 fd, 加入到 fd 管理中
        '''
        while 1:
            try:
                # 接收监听获取到的新 socket
                new_socket, addr = self.listen_fd.accept()
                new_socket.setblocking(0)
                new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # 添加到 fd 管理
                self.fd_manager.new(addr, new_socket, self.events)
            except socket.error as e:
                break

    def __event_receive(self, fd):
        self.logger.info("func=receive addr={} port={}".format(*self.fd_manager[fd].address))
        try:
            self.fd_manager.receive(fd)
            self.epoll_fd.modify(fd, self.events | select.EPOLLOUT)
        except socket.error as e:
            self.logger.error(str(e))
            del self.fd_manager[fd]

        self.task_manager.new(self.__task.on_receive, fd)

    def __event_send(self, fd):
        self.logger.info("func=send addr={} port={}".format(*self.fd_manager[fd].address))
        try:
            self.fd_manager.send(fd)
            self.epoll_fd.modify(fd, self.events)
        except socket.error as e:
            self.logger.error(str(e))
            del self.fd_manager[fd]

        self.task_manager.new(self.__task.on_send, fd)

    def __event_error(self, fd):
        del self.fd_manager[fd]

    def run(self):
        '''epoll 的主循环, 会依据事件进行对应操作
        '''
        if self.epoll_fd is None:
            self.__init_epoll()

        event_dict = {
            select.EPOLLIN: self.__event_receive,
            select.EPOLLOUT: self.__event_send,
            select.EPOLLHUP: self.__event_error,
            select.EPOLLERR: self.__event_error,
        }

        while 1:
            # 等待 epoll 抛出事件
            epoll_list = self.epoll_fd.poll()

            for fd, events in epoll_list:
                if fd == self.listen_fd.fileno():  # 新建
                    self.__event_new()
                else:
                    try:
                        event_dict[events](fd)
                    except KeyError:
                        continue

                self.__check_timeout(fd)

    def __check_timeout(self, fd):
        '''检查是否超时, 超时的计算是处理完请求的时间与上一次操作的时间的差
        如果超时则删除该 fd, 如果没超时则更新上一次操作时间为现在

        参数:
            fd:  指定文件描述子
        '''
        fd_info = self.fd_manager.get(fd)
        if fd_info is None:
            return
        now = time.time()
        # 超时
        if now - fd_info.timestamp > self.timeout:
            del self.fd_manager[fd]
        else:
            fd_info.timestamp = now
