#!/user/bin/env python
# -*- encoding:utf-8 -*-


class TaskInterface(object):

    def __init__(self, fd_info):
        self.__fd_info = fd_info

    def fd_info(self):
        return self.__fd_info

    def run(self, data):
        pass
