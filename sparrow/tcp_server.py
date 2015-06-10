#!/user/bin/env python
# -*- encoding: UTF-8 -*-
import stackless
import multiprocessing
import socket
import os
import sys

import tasks
import loop
import log

logger = log.get_logger()


class TcpServer(object):
    '''基于 stackless 的封装好的 TCP 服务器.

    支持如下操作:
        1. 接收数据完毕的回调函数: on_receive
        2. 发送数据完毕的回调函数: on_send
        3. 使用 fd_manager 可完成如下操作:
            3.1. 发送数据: fd_manager.send(fd, data)
            3.2. 接收数据: fd_manager.receive(fd)
            3.3. 删除 fd: fd_manager.remove(fd)
            3.4. 弹出接收到的数据: fd_manager.pop_received_data(fd)
    '''

    def __init__(self, port, timeout, tasklet_num):
        '''初始化

        参数:
            port: 监听端口
            timeout: 超时时长 (ms)
            tasklet_num: 微线程个数
        '''
        self.__timeout = timeout

        self.__task_channel = stackless.channel()
        self.__init_tasklets(tasklet_num)
        self.__listen_fd = self.__init_listener(port)

    def __init_tasklets(self, tasklet_num):
        '''初始化微线程, 并开启. 每个微线程都绑定 __process 函数

        参数:
            tasklet_num: 微线程个数
        '''
        for i in xrange(tasklet_num):
            task = stackless.tasklet()
            task.bind(self.__process)
            task.setup()
        logger.info("{} tasklets initialized".format(tasklet_num))

    def __process(self):
        '''每个微线程的主循环
        '''
        while 1:
            task = self.__task_channel.receive()
            if isinstance(task, tasks.ReceiveTask):
                self.on_receive(task.fd)
            elif isinstance(task, tasks.SendTask):
                self.on_send(task.fd)

    def __init_listener(self, port):
        '''初始化监听 socket

        参数:
            port: 监听端口
        '''
        reload(sys)
        sys.setdefaultencoding("utf8")

        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_fd.bind(('', port))
        listen_fd.listen(1024)
        listen_fd.setblocking(0)
        logger.info("initialize listener finished, port={}".format(port))
        return listen_fd

    def __single_process_run(self):
        '''单进程启动
        IO Loop 也是使用 tasklet 启动的一个 "微线程"
        '''
        loop_obj = loop.Loop(self.__listen_fd, self.__timeout,
                             self.__task_channel)
        task = stackless.tasklet()
        task.bind(loop_obj.run)
        task.setup()
        stackless.run()

    def run(self, process_num=1):
        '''支持多进程和单进程启动

        参数:
            process_num: 进程数, 默认为1, 如果设置为0则依据 CPU 核数决定
        '''
        if process_num == 0:
            process_num = multiprocessing.cpu_count()

        if process_num > 1:
            for i in xrange(process_num):
                new_pid = os.fork()
                if new_pid == 0:
                    self.__single_process_run()
        self.__single_process_run()
        logger.info("{} processes started".format(process_num))

    def on_receive(self, fd):
        '''接收完毕后的操作
        '''
        pass

    def on_send(self, fd):
        '''发送完毕后的操作
        '''
        pass
