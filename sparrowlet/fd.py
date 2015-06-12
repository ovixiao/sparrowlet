#!/user/bin/env python
# -*- encoding:utf-8 -*-
import socket
import time
import errno

import log
import buff


logger = log.get_logger()


# 单例模型
def singleton(cls, *args, **kargs):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kargs)
        return instances[cls]
    return _singleton


class FdInfo(object):
    '''包含文件描述子的需要的信息. 文件描述子既可以描述一个接收的 socket,
    也可以描述一个发送的 socket.
    '''

    def __init__(self, address, new_socket):
        '''新建一个文件描述子, 初始化对应的 socket

        参数:
            address: 远端 IP 地址
            new_socket: fd 描述的 socket 实例
            timestamp: 上次操作的时间戳
            sending_data: 待发送的数据
            received_data: 已经接收到的数据
        '''
        self.address = address
        self.socket = new_socket
        self.timestamp = time.time()
        self.sending_data = buff.Buff()
        self.received_data = buff.Buff()

        self.__init_socket()

    def __del__(self):
        '''关闭 socket
        '''
        try:
            self.socket.close()
        except Exception as e:
            logger.error(str(e))

    def __init_socket(self):
        '''初始化 socket
        修改为非租塞模式, 使用 TCP 协议
        '''
        # 非租塞模式
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def receive(self):
        '''接收所有的数据, 并保存数据
        如果存在问题会抛出异常
        '''
        # 修改上次操作时间
        self.timestamp = time.time()
        while 1:
            try:
                data = self.socket.recv(1024)
                if data:
                    self.received_data.append(data)
                else:  # 传输完毕
                    return
            except socket.error as e:
                # 暂时没数据传输了, 空出 CPU
                if e.errno == errno.EAGAIN:
                    return
                else:
                    raise e

    def send(self, data=None):
        '''传送所有的待传送数据
        如果存在问题会抛出异常
        '''
        # 修改上次操作时间
        self.timestamp = time.time()
        if isinstance(data, str):
            self.sending_data.append(data)

        # 没有数据要传送
        if len(self.sending_data) == 0:
            return

        send_len = 0  # 已经发送完的数据长度
        sending_data = self.sending_data.pop_str()
        while send_len < len(sending_data):
            try:
                send_len += self.socket.send(sending_data[send_len:])
            except socket.errno as e:
                # 暂时不传输数据了, 空出 CPU
                if e.errno == errno.EAGAIN:
                    self.sending_data.append(sending_data[send_len:])
                    return
                else:
                    raise e


@singleton
class FdManager(dict):
    '''继承自字典 dict 的类, 实现了如下功能:
    1. 新建: new
    2. 删除指定 fd: __delitem__
    3. 指定 fd 接收数据: receive
    4. 指定 fd 发送数据: send
    '''

    def __init__(self, *args, **kargv):
        '''初始化

        参数:
            io_fd: io 的文件描述子
        '''
        dict.__init__(self, *args, **kargv)

    def __delitem__(self, fd):
        ''' 删除某 fd, 包括如下操作:
        1. 从 io 中注销
        2. 关闭 fd 对应的 socket
        3. 删除管理信息 (fd_info_dict)
        如果不存在 fd 会自动忽略

        参数:
            fd: 文件描述子
        '''
        # 删除管理信息
        fd_info = self.get(fd, None)
        if fd_info is not None:
            dict.__delitem__(self, fd)
            del fd_info

        # 从 io 中注销
        try:
            self.__io_fd.unregister(fd)
            pass
        except Exception as e:
            logger.error(str(e))
            pass

    def __setitem__(self, fd, fd_info):
        '''重载超类的 __setitem__ 方法, 添加了对象判断.
        如果不是 FdInfo 对象则抛出 ValueError 异常.

        参数:
            fd: 文件描述子
            fd_info: FdInfo 实例
        '''
        if not isinstance(fd_info, FdInfo):
            raise ValueError
        dict.__setitem__(self, fd, fd_info)

    def set_io(self, io_fd):
        self.__io_fd = io_fd

    def new(self, address, new_socket, events):
        '''创建一个新的 fd->fd_info 映射

        参数:
            address: 远端 IP 地址
            socket: 新建 fd 的 socket
        '''
        # 注册事件和 socket 到 eopll
        fd = new_socket.fileno()
        self.__io_fd.register(fd, events)
        fd_info = FdInfo(address, new_socket)
        self[fd] = fd_info

    def receive(self, fd):
        '''指定 fd 接收数据

        参数:
            fd: 指定文件描述子
        '''
        fd_info = self.get(fd)
        if fd_info is None:
            logger.error("Invalid fd {fd}".format(fd=fd))
            return

        fd_info.receive()

    def send(self, fd, data=None):
        '''指定 fd 传送数据

        参数:
            fd: 指定文件描述子
        '''
        fd_info = self.get(fd)
        if fd_info is None:
            logger.error("Invalid fd {fd}".format(fd=fd))
            return

        fd_info.send(data)

    def remove(self, fd):
        self.__delitem__(fd)

    def pop_received_data(self, fd):
        fd_info = self.get(fd)
        if fd_info is None:
            logger.error("Invalid fd {fd}".format(fd=fd))
            return

        return fd_info.received_data.pop_str()

    def append_received_data(self, fd, data):
        fd_info = self.get(fd)
        if fd_info is None:
            logger.error("Invalid fd {fd}".format(fd=fd))
            return

        fd_info.received_data.append(data)
