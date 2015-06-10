#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sparrow

class Test(sparrow.UriInterface):

    def get(self):
        return "hello world"

    def post(self):
        pass


if __name__ == '__main__':
    port = 8888
    timeout = 10
    tasklet_num = 10
    svr = sparrow.HttpServer(port, timeout, tasklet_num)
    svr.register({'/test': Test})
    svr.run()
