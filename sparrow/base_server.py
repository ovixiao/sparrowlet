#!/user/bin/env python
# -*- encoding: UTF-8 -*-
import stackless
import multiprocessing
import socket
import os
import sys

import tasks
import loop


class BaseServer():
    '''基于 stackless 的服务基类

    对外的操作包括:
         新建任务: new()
    '''

    def __init__(self, port, timeout, tasklet_num, process_num=0):
        '''初始化

        参数:
            tasklet_num: 微线程个数
        '''
        self.__process_num = process_num
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
        stackless.run()

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
        listen_fd.listen(10240)
        listen_fd.setblocking(0)
        return listen_fd

    def run(self):
        '''多进程启动
        '''
        if self.__process_num == 0:
            self.__process_num = multiprocessing.cpu_count()

        if self.__process_num > 1:
            for i in xrange(self.__process_num):
                new_pid = os.fork()
                loop_pid = loop.Loop(self.__listen_fd, self.__timeout,
                                     self.__task_channel)
                loop_pid.run()
        loop_pid = loop.Loop(self.__listen_fd, self.__timeout,
                             self.__task_channel)
        loop_pid.run()

    def on_receive(self, fd):
        '''接收完毕后的操作
        '''
        pass

    def on_send(self, fd):
        '''发送完毕后的操作
        '''
        pass
