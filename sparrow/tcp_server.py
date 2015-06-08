#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sys
import log
import os
import socket

import loop
import base_server
import fd


fd_manager = fd.FdManager()
logger = log.get_logger()


class TcpServer(base_server.BaseServer):
    '''封装好的 TCP 服务器.
    支持如下操作:
        1. 接收数据完毕的回调函数: on_receive
        2. 发送数据完毕的回调函数: on_send
        3. 使用 fd_manager 可完成如下操作:
            3.1. 发送数据: fd_manager.send(fd, data)
            3.2. 接收数据: fd_manager.receive(fd)
            3.3. 删除 fd: fd_manager.remove(fd)
            3.4. 弹出接收到的数据: fd_manager.pop_received_data(fd)
    '''

    def on_receive(self, fd):
        pass

    def on_send(self, fd):
        pass
