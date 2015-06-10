#!/user/bin/env python
# -*- encoding:utf-8 -*-
import urllib
import copy

import tcp_server
import log
import fd


logger = log.get_logger()
fd_manager = fd.FdManager()


class HttpData(object):
    '''用于保存处理过后的 HTTP 请求数据
    '''

    def __init__(self):
        self.version = None  # HTTP 版本
        self.uri = None  # HTTP 请求的 URI
        self.raw_uri = None  # HTTP 的原始 URI, 包含参数
        self.method = None  # 请求方式 POST/GET
        self.content = None  # 正文数据
        self.headers = {}  # 头信息字典
        self.get_params = {}  # GET 信息字典


class HttpServer(tcp_server.TcpServer):
    '''基于 stackless 的简单 HTTP 服务器.

    会响应的 URI 需要通过 register 函数来注册.
    '''

    def __init__(self, port, timeout, tasklet_num):
        '''初始化

        参数:
            port: 监听端口
            timeout: 超时时长 (ms)
            tasklet_num: 微线程个数
        '''
        tcp_server.TcpServer.__init__(self, port, timeout, tasklet_num)
        # 储存 URI 对应关系的词典
        self.uri_dict = {}
        # 默认的 HTTP 头
        self.__default_send_header = {
            'Content-Type': 'text/html;charset=utf-8',
            'Connection': 'keep-alive',
        }
        # 404 返回的结果
        self.__404 = self.__format("404 Not Found", "404 Not Found")
        # 400 返回的结果
        self.__400 = self.__format("400 Bad Request", "400 Bad Request")

    def __parse_header(self, line, index, http_data):
        '''解析 HTTP 的头信息

        参数:
            line: 头信息的一行数据
            index: 头信息的行号, 从0开始
            http_data: 保存处理完后信息的对象
        '''
        # 第一行信息比较特殊
        if index == 0:
            # 如果这里报错链接关闭, 因为数据解析位置已经出错
            method, uri, version = line.split(' ')
            http_data.method = method
            http_data.raw_uri = uri
            self.__parse_uri(uri, http_data)
            http_data.version = version
            return

        # 其余行数据格式比较固定
        try:
            key, value = line.split(':', 1)
        except ValueError:
            return

        key = urllib.unquote(key.strip())
        value = urllib.unquote(value.strip())
        # 如果有重复只保留最后一个
        http_data.headers[key] = value

    def __parse_uri(self, uri, http_data):
        '''解析 URI

        参数:
            uri: 从 HTTP 头中获取的 URI
            http_data: 保存处理完后信息的对象
        '''
        # 如果不包含参数就直接 return
        try:
            beg_index = uri.index('?')
        except ValueError:
            http_data.uri = urllib.unquote(uri)
            return

        get_line = uri[beg_index + 1:]
        http_data.uri = urllib.unquote(uri[: beg_index])
        for pair in get_line.split('&'):
            try:
                key, value = pair.split("=")
            except ValueError:
                continue

            key = urllib.unquote(key.strip())
            value = urllib.unquote(value.strip())
            # 如果有重复只保留最后一个
            http_data.get_params[key] = value

    def __parse_content(self, content, http_data):
        '''解析 content. 依据头信息中的 Content-Length 判断是否已经接收完毕.

        参数:
            content: HTTP 正文
            http_data: 保存处理完后信息的对象
        '''
        # 如果不包含 Content-Length 就意味着没有 content.
        content_length = 0
        keys = ('Content-Length', 'content-length')
        for key in keys:
            http_data.headers.get(key)
            if content_length is not None:
                break

        left_data = None
        if content_length <= len(content):
            # 保存正文数据
            http_data.content = content[:content_length]
            left_data = content[content_length:]
        else:
            left_data = content
        # 把多余的数据存放进 FdInfo, 留着下次用
        fd_manager.append_received_data(fd, left_data)

    def __parse(self, data, http_data):
        '''解析的入口函数.

        如果 http_data 中的 content 是 None, 则表示没有接收完整数据.

        参数:
            data: 收取到的数据, 可能完整可能不完整.
            http_data: 保存处理完后信息的对象
        '''
        beg_index, end_index = 0, 0

        index = 0
        go_on = False
        while 1:
            # 查找每一个分行
            try:
                end_index = data.index('\r\n', beg_index)
            except ValueError:
                break

            # 连续2个\r\n, 之后的都是正文数据.
            # 正文处理过后这轮请求的边界就已经处理完了
            if beg_index == end_index:
                self.__parse_content(data[beg_index + 2:], http_data)
                # 如果有
                go_on = True
                break

            # 头信息
            line = data[beg_index: end_index]
            self.__parse_header(line, index, http_data)
            beg_index = end_index + 2
            index += 1

    def __format(self, content, code="200 OK", header=None):
        '''格式化 HTTP 返回结果

        参数:
            content: 返回的正文
            code: 返回的错误码
            header: 返回的头, 如果为 None 自动使用默认头信息
        '''
        if header is None:
            header = copy.copy(self.__default_send_header)
        # 添加长度
        header['Content-Length'] = str(len(content))
        # 将字典信息变成一行
        header_line = "\r\n".join([": ".join(x) for x in header.items()])

        return 'HTTP/1.1 {}\r\n{}\r\n\r\n{}'.format(code, header_line, content)

    def register(self, uri_dict):
        '''注册处理对应 uri 的类

        参数:
            uri_dict: URI 与处理的类的对应词典
        '''
        self.uri_dict.update(uri_dict)

    def on_receive(self, fd):
        '''接收到数据后的操作
        '''
        # 分析获取到的数据
        data = fd_manager.pop_received_data(fd)
        http_data = HttpData()

        try:
            self.__parse(data, http_data)
        except Exception as e:
            print e
            logger.error("{fd} received data error".format(fd=fd))
            fd_manager.remove(fd)
            return

        # 数据还没接收完毕
        if http_data.content is None:
            return

        method = http_data.method.lower()
        uri_cls = self.uri_dict.get(http_data.uri)
        send_data = None

        # 页面不存在
        if uri_cls is None:
            send_data = self.__404
        else:
            uri_obj = uri_cls(http_data)
            if method == 'get':
                logger.info(" ".join((fd_manager[fd].address[0],
                                      method, http_data.raw_uri)))
                send_data = uri_obj.get()
                send_data = self.__format(send_data)
            elif method == 'post':
                logger.info(" ".join((fd_manager[fd].address[0],
                                      method, http_data.raw_uri)))
                send_data = uri_obj.post()
                send_data = self.__format(send_data)
            else:  # 既不是 GET 也不是 POST, 那是什么鬼?
                send_data = self.__400

        if send_data:
            fd_manager.send(fd, send_data)

    def on_send(self, fd):
        ''' 发送完后关闭连接
        '''
        fd_manager.remove(fd)
