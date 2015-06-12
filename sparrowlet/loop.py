#!/user/bin/env python
# -*- encoding:utf-8 -*-
import select
import time

import log
import fd
import socket
import tasks


# 包装了一层的事件
EVENT_READ = select.POLLIN
EVENT_WRITE = select.POLLOUT
EVENT_ERR = select.POLLERR | select.POLLHUP

# 命令
CMD_ONRECEIVE = 0x01
CMD_ONSEND = 0x02

# 全局定义的单例对象
fd_manager = fd.FdManager()
logger = log.get_logger()


class Loop(object):
    '''服务端循环对应的类
    包含了如下几种操作的服务端:
    1. 删除: remove
    2. 新建: new
    3. 发送数据: send
    4. 接受数据: receive
    '''

    def __init__(self, listen_fd, timeout, task_channel):
        '''初始化

        参数:
            listen_fd: 监听 socket
            timeout: 超时时长
            task_channel: 传递任务的通道
        '''
        # 传入的参数
        self.timeout = timeout
        self.listen_fd = listen_fd
        #  响应的事件
        self.events = EVENT_READ | EVENT_ERR
        # io 的文件描述子
        self.io_fd = None
        self.__init_io()
        # 文件描述子管理器
        fd_manager.set_io(self.io_fd)
        # 任务管道
        self.task_channel = task_channel

    def __init_listen(self, port):
        '''初始化监听 socket

        参数:
            port: 监听端口
        '''
        self.listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_fd.setblocking(0)
        self.listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_fd.bind(('', port))
        self.listen_fd.listen(1024)

    def __init_io(self):
        '''初始化 io, 注册各种操作 event
        '''
        try:
            self.io_fd = select.epoll()
        except AttributeError:
            self.io_fd = select.poll()

        try:
            self.io_fd.register(self.listen_fd.fileno(), self.events)
        except select.error as e:
            logger.critical(str(e))
            self.io_fd = None

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
                new_socket.setsockopt(socket.SOL_SOCKET,
                                      socket.SO_REUSEADDR, 1)
                # 添加到 fd 管理
                fd_manager.new(addr, new_socket, self.events)
            except socket.error as e:
                break

    def __event_receive(self, fd):
        try:
            fd_manager.receive(fd)
            self.io_fd.modify(fd, self.events | EVENT_WRITE)
        except socket.error as e:
            logger.error(str(e))
            fd_manager.remove(fd)

        self.task_channel.send(tasks.ReceiveTask(fd))

    def __event_send(self, fd):
        try:
            fd_manager.send(fd)
            self.io_fd.modify(fd, self.events)
        except socket.error as e:
            logger.error(str(e))
            fd_manager.remove(fd)

        self.task_channel.send(tasks.SendTask(fd))

    def __event_error(self, fd):
        fd_manager.remove(fd)

    def __check_timeout(self, fd):
        '''检查是否超时, 超时的计算是处理完请求的时间与上一次操作的时间的差
        如果超时则删除该 fd, 如果没超时则更新上一次操作时间为现在

        参数:
            fd:  指定文件描述子
        '''
        fd_info = fd_manager.get(fd)
        if fd_info is None:
            return
        now = time.time()
        # 超时
        if now - fd_info.timestamp > self.timeout:
            fd_manager.remove(fd)
        else:
            fd_info.timestamp = now

    def run(self):
        '''io 的主循环, 会依据事件进行对应操作
        '''
        if self.io_fd is None:
            self.__init_io()

        while 1:
            # 等待 io 抛出事件
            io_list = self.io_fd.poll()

            for fd, events in io_list:
                if fd == self.listen_fd.fileno():  # 新建
                    self.__event_new()
                elif events & EVENT_READ:  # 读操作
                    self.__event_receive(fd)
                elif events & EVENT_WRITE:  # 写操作
                    self.__event_send(fd)
                elif events & EVENT_ERR:  # 错误
                    self.__event_error(fd)
                else:  # 其他情况,  暂不考虑
                    continue

                # 检测超时
                self.__check_timeout(fd)
