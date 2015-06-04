#!/user/bin/env python
# -*- encoding:utf-8 -*-
import urllib

class Http(object):
    '''暂时够用的 HTTP 协议.
    '''

    def __init__(self):
        self.header_params = {}
        self.get_params = {}

    def parse(self, data):
        '''总体的解析函数

        参数:
            data: 获取到的 TCP 数据
        '''
        self.clean()
        headers = self.__parse_raw_data(data)
        self.__parse_header(headers)
        self.__parse_uri()
        self.__parse_content()

    def __parse_content(self):
        content_len = int(self.header_params.get('Content-Length', 0))
        self.left_data = self.content[content_len: ]
        self.content = self.content[: content_len]

    def __parse_raw_data(self, data):
        '''解析原始数据

        参数:
            data: 获取到的 TCP 数据
        '''
        beg_index = 0
        end_index = 0
        headers = []
        self.content = None

        while 1:
            try:
                end_index = data.index('\r\n', beg_index)
            except ValueError:
                break

            line = data[beg_index: end_index]
            if line == '':
                self.content = data[end_index + 2:]
                break
            else:
                headers.append(line)
                beg_index = end_index + 2

        return headers

    def __parse_header(self, headers):
        '''解析 HTTP 头

        参数:
            header: 头信息总体数据
        '''
        self.method, self.uri, self.version = headers[0].split(' ')
        for header in headers[1:-1]:
            try:
                key, value = header.split(":", 1)
            except ValueError:
                continue

            key = urllib.unquote(key.strip())
            value = urllib.unquote(value.strip())
            self.header_params[key] = value

    def __parse_uri(self):
        '''解析 URI
        '''
        try:
            beg_index = self.uri.index('?')
        except ValueError:
            return

        get_line = self.uri[beg_index + 1: ]
        self.uri = urllib.unquote(self.uri[:beg_index])
        get_params = get_line.split("&")
        for param in get_params:
            try:
                key, value = param.split("=")
            except ValueError:
                continue

            key = urllib.unquote(key.strip())
            value = urllib.unquote(value.strip())
            self.get_params[key] = value

    def format(self, header, content):
        header['Content-Length'] = str(len(content))
        header = '\r\n'.join([': '.join(x) for x in header.items()])
        ret_str = 'HTTP/1.1 200 OK\r\n{header}\r\n\r\n{content}'.format(
            header=header, content=content)
        return ret_str

    def clean(self):
        self.header_params = {}
        self.get_params = {}
        self.content = ''
        self.left_data = ''

    def output(self):
        print "uri:", self.uri
        print "method:", self.method
        print "version:", self.version
        print "get:", self.get_params
        print "header:", self.header_params
        print "content", self.content


if __name__ == '__main__':
    http = Http()
    http.parse(test_string)
