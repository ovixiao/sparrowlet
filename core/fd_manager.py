#!/user/bin/env python
# -*- encoding:utf-8 -*-
import socket
from fd_info import FdInfo


class FdManager(dict):
    '''继承自字典 dict 的类, 实现了如下功能:
    1. 新建: new
    2. 删除指定 fd: __delitem__
    3. 指定 fd 接收数据: receive
    4. 指定 fd 发送数据: send
    '''

    def __init__(self, epoll_fd, *args, **kargv):
        '''初始化

        参数:
            epoll_fd: epoll 的文件描述子
        '''
        dict.__init__(self, *args, **kargv)
        self.__epoll_fd = epoll_fd

    def new(self, address, new_socket, events):
        '''创建一个新的 fd->fd_info 映射

        参数:
            address: 远端 IP 地址
            socket: 新建 fd 的 socket
        '''
        # 注册事件和 socket 到 eopll
        fd = new_socket.fileno()
        self.__epoll_fd.register(fd, events)
        fd_info = FdInfo(address, new_socket)
        self[fd] = fd_info

    def __delitem__(self, fd):
        ''' 删除某 fd, 包括如下操作:
        1. 从 epoll 中注销
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
            fd_info.clean_fd()

        # 从 epoll 中注销
        try:
            self.__epoll_fd.unregister(fd)
        except Exception as e:
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

    def receive(self, fd):
        '''指定 fd 接收数据

        参数:
            fd: 指定文件描述子
        '''
        fd_info = self.get(fd)
        if fd_info is None:
            return

        fd_info.receive()
        data = fd_info.received_data

    def send(self, fd, data=None):
        '''指定 fd 传送数据

        参数:
            fd: 指定文件描述子
        '''
        fd_info = self.get(fd)
        if fd is None:
            return

        fd_info.send(data)
