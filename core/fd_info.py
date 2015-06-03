#!/user/bin/env python
# -*- encoding:utf-8 -*-
import time
import socket
import errno
import logging


class FdInfo(object):
    '''包含文件描述子的需要的信息. 文件描述子既可以描述一个接收的 socket,
    也可以描述一个发送的 socket.
    '''

    MAX_RECV_SIZE = 1024  # 每次接收数据的最大长度

    def __init__(self, address, new_socket):
        '''新建一个文件描述子, 初始化对应的 socket

        参数:
            address: 远端 IP 地址
            new_socket: fd 描述的 socket 实例
            timestamp: 上次操作的时间戳
            sending_data: 待发送的数据
            __received_data_list: 已经接收到的数据, 因为每次接收都是一串字符串,
                                  如果直接进行字符串拼接时间消耗比较大,
                                  所以存放到列表中
        '''
        self.address = address
        self.socket = new_socket
        self.timestamp = time.time()
        self.sending_data = ''
        self.__received_data_list = []
        self.__init_socket()
        self.logger = logging.getLogger()

    def __del__(self):
        '''关闭 socket
        '''
        try:
            if self.socket:
                self.socket.close()
        except Exception as e:
            self.logger.error(str(e))
            pass

    def __init_socket(self):
        '''初始化 socket
        修改为非租塞模式, 使用 TCP 协议
        '''
        # 非租塞模式
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    @property
    def received_data(self):
        '''拼接接收到的字符串并返回
        为了节省时间, 每次调用的时候才拼接一次. 并且保存拼接好的数据.

        返回:
            返回拼接好的字符串
        '''
        data = ''.join(self.__received_data_list)
        self.__received_data_list = []
        return data

    def receive(self):
        '''接收所有的数据, 并保存数据
        如果存在问题会抛出异常
        '''
        # 修改上次操作时间
        self.timestamp = time.time()
        while 1:
            try:
                data = self.socket.recv(self.__class__.MAX_RECV_SIZE)
                if data:
                    self.__received_data_list.append(data)
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
            self.sending_data += data

        # 没有数据要传送
        if len(self.sending_data) == 0:
            return

        send_len = 0  # 已经发送完的数据长度
        while 1:
            try:
                send_len += self.socket.send(self.sending_data[send_len:])
                # 全部传送完毕
                if send_len == len(self.sending_data):
                    self.sending_data = ''
                    return
            except socket.errno as e:
                # 暂时不传输数据了, 空出 CPU
                if e.errno == errno.EAGAIN:
                    self.sending_data = self.sengding_data[send_len:]
                    return
                else:
                    raise e

    def clean_fd(self):
        '''清空 fd
        '''
        self.socket.close()
        self.socket = None
