#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sys
import core


class Task(core.TaskInterface):

    def run(self, data):
        print data


def main():
    reload(sys)
    sys.setdefaultencoding("utf8")

    port = 8888
    timeout = 10
    svr = core.Loop(port, timeout, Task)
    svr.run()


if __name__ == '__main__':
    main()
