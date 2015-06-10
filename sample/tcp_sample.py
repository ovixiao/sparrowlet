#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sparrow

fd_manager = sparrow.FdManager()

class Svr(sparrow.TcpServer):

    def on_receive(self, fd):
        fd_manager.send(fd, "hello world!")

    def on_send(self, fd):
        fd_manager.remove(fd)


if __name__ == '__main__':
    port = 8888
    timeout = 10
    tasklet_num = 10
    svr = Svr(port, timeout, tasklet_num)
    svr.run(0)
