#!/user/bin/env python
# -*- encoding:utf-8 -*-
'''
用于在通道中传输的任务
'''


class SendTask(object):
    '''发送任务
    '''

    def __init__(self, fd):
        self.fd = fd


class ReceiveTask(object):
    '''接收任务
    '''

    def __init__(self, fd):
        self.fd = fd
