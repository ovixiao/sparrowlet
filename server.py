#!/user/bin/env python
# -*- encoding:utf-8 -*-
'''
基于 epoll 的 TCP 简单网络框架.
'''
import socket
import select
import time
from fd_manager import FdManager
from fd_info import FdInfo
import sys


class Server(object):
    '''服务端对应的类
    包含了如下几种操作的服务端:
    1. 删除: remove
    2. 新建: new
    3. 发送数据: send
    4. 接受数据: receive
    '''

    def __init__(self, listen_fd, timeout):
        '''初始化

        参数:
            listen_fd: 监听 fd
            timeout: 超时时长
        '''
        # 传入的参数
        self.listen_fd = listen_fd
        self.timeout = timeout
        #  响应的事件
        self.events = (select.EPOLLIN | select.EPOLLET | select.EPOLLERR |
            select.EPOLLHUP)
        # epoll 的文件描述子
        self.epoll_fd = None
        self.init_epoll()
        # 文件描述子管理器
        self.fd_manager = FdManager(self.epoll_fd)

    def new(self):
        ''' 创建一个新的 fd, 会进行如下操作:
        1. 接收监听 socket
        2. 创建新的 fd, 加入到 fd 管理中
        '''
        while 1:
            try:
                # 接收监听获取到的新 socket
                new_socket, addr = self.listen_fd.accept()
                # 添加到 fd 管理
                self.fd_manager.new(addr, new_socket, self.events)
            except socket.error as e:
                break

    def init_epoll(self):
        '''初始化 epoll, 注册各种操作 event
        '''
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.listen_fd.fileno(), self.events)
        except select.error as e:
            self.epoll_fd = None

    def epoll_loop(self):
        '''epoll 的主循环, 会依据事件进行对应操作
        '''
        if self.epoll_fd is None:
            self.init_epoll()

        while 1:
            # 等待 epoll 抛出事件
            epoll_list = self.epoll_fd.poll()

            for fd, events in epoll_list:
                if fd == self.listen_fd.fileno():  # 新建
                    self.new()
                elif select.EPOLLIN & events:  # 接收
                    try:
                        self.fd_manager.receive(fd)
                    except socket.error as e:
                        del self.fd_manager[fd]
                elif select.EPOLLOUT & events:  # 传送
                    try:
                        self.fd_manager.send(fd)
                    except socket.error as e:
                        del self.fd_manager[fd]
                elif select.EPOLLHUP & events or select.EPOLLERR & events:
                    del self.fd_manager[fd]
                else:
                    continue

                self.check_timeout(fd)


    def check_timeout(self, fd):
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
