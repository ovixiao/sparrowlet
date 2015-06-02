#!/user/bin/env python
# -*- encoding:utf-8 -*-


class TaskInterface(object):

    def __init__(self, fd_manager):
        self.__fd_manager = fd_manager

    def fd_info(self, fd):
        return self.__fd_manager[fd]

    def on_receive(self, fd):
        pass

    def on_send(self, fd):
        pass
