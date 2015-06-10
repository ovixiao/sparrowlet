#!/user/bin/env python
# -*- encoding:utf-8 -*-
import sparrow


class Test(sparrow.UriInterface):

    def get(self):
        '''GET 方式发起请求的返回结果
        '''
        return "hello GET"

    def post(self):
        '''POST 方式发起请求的返回结果
        '''
        return "hello POST"


if __name__ == '__main__':
    port = 8888
    timeout = 10
    tasklet_num = 10
    svr = sparrow.HttpServer(port, timeout, tasklet_num)
    # 注册 URI 的对应逻辑处理类
    uri_dict = {
        '/test': Test
    }
    svr.register(uri_dict)
    # 可以带参数0来自适应开启多进程, 也可以指定进程数
    svr.run()
