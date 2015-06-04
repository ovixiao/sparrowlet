test_string = '''GET /%E3%82%A4%E3%83%A4%E3%83%9B%E3%83%B3%E3%83%BB%E3%83%98%E3%83%83%E3%83%89%E3%83%9B%E3%83%B3-%E3%82%AB%E3%83%8A%E3%83%AB-%E3%82%AA%E3%83%BC%E3%83%90%E3%83%BC%E3%83%98%E3%83%83%E3%83%89-%E3%82%AA%E3%83%BC%E3%83%87%E3%82%A3%E3%82%AA/b/ref=dp_bc_4?ie=UTF8&node=3477981 HTTP/1.1\r\nHost: 172.17.195.175:8888\r\nConnection: keep-alive\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36\r\nAccept: */*\r\nDNT: 1\r\nReferer: http://172.17.195.175:8888/\r\nAccept-Encoding: gzip, deflate, sdch\r\nAccept-Language: zh-CN,zh;q=0.8,ja;q=0.6,en;q=0.4\r\n\r\ncontent\r\n
'''
import urllib

class Http(object):

    def __init__(self):
        self.header_params = {}
        self.get_params = {}

    def parse(self, data):
        headers = self.__parse_raw_data(data)
        self.__parse_header(headers)
        self.__parse_uri()

    def __parse_raw_data(self, data):
        beg_index = 0
        end_index = 0
        headers = []
        self.body = None

        while 1:
            try:
                end_index = data.index('\r\n', beg_index)
            except ValueError:
                break

            line = data[beg_index: end_index]
            if line == '':
                self.body = data[end_index + 2: -2]
                break
            else:
                headers.append(line)
                beg_index = end_index + 2

        return headers

    def __parse_header(self, headers):
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


if __name__ == '__main__':
    http = Http()
    http.parse(test_string)
    print "uri:", http.uri
    print "method:", http.method
    print "version:", http.version
    print "get:", http.get_params
    print "header:", http.header_params
    print "body", http.body

