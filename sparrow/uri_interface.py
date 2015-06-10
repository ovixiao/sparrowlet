#!/user/bin/env python
# -*- encoding:utf-8 -*-


class UriInterface(object):
    '''URI 的接口类, 用来处理逻辑事件.

    定义了2个方法:
        get: 用来处理 GET 方式的请求, **返回值作为发送数据**.
        post: 用来处理 POST 方式的请求, **返回值作为发送数据**.

    可以直接使用 self.http_data 来获取 http 请求的数据,
    详细请看 http_server.py 的 HttpData 类的定义.
    '''

    def __init__(self, http_data):
        self.http_data = http_data

    def get(self):
        pass

    def post(self):
        pass
