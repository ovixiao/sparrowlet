#!/user/bin/env python
# -*- encoding: UTF-8 -*-
import stackless


class TaskManager():
    '''基于 stackless 的任务管理器

    对外的操作包括:
         新建任务: new()
    '''

    def __init__(self, tasklet_num):
        '''初始化

        参数:
            tasklet_num: 微线程个数
        '''
        self.__channel = stackless.channel()
        self.__init_tasklets(tasklet_num)

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
            func, args, kargs = self.__channel.receive()
            func(*args, **kargs)

    def new(self, func, *args, **kargs):
        '''新建一个任务, 投入信号通道

        参数:
            func: 要运行的函数

        参数:
            tasklet_num: 微线程个数
        '''
        self.__channel = stackless.channel()
        self.__init_tasklets(tasklet_num)

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
            func, args, kargs = self.__channel.receive()
            func(*args, **kargs)

    def new(self, func, *args, **kargs):
        '''新建一个任务, 投入信号通道

        参数:
            func: 要运行的函数
            *args, **kargs: 函数的参数
        '''
        self.__channel.send((func, args, kargs))
