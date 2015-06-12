# Sparrowlet
一个简单又实用的 TCP 服务器, 主要是基于 epoll 进行 IO select, 所以最好还是在 linux 上进行.
其余基于 poll 的纯粹是为了能在 mac 上能调试.


## 1. 依赖

1. 为了提高运行效率, 使用 [stackless python](http://www.stackless.com/) 来做 "多线程".


## 2. 日志

默认的日志路径位于 log 目录下的 sparrowlet.log, 由于使用了多进程, 所以不能用 logging 来做日期文件分割,
可使用如下代码来进行分割:

```shell
DATE=`date +%Y%m%d`
cp sparrowlet.log sparrowlet.log.${DATE}
echo > sparrowlet.log
```

做成定时任务, 每天零点运行.

日志的主要使用层级为:
>   1. INFO: 表示某一次性的任务完成, 例如完成一次 HTTP 请求.
>   2. ERROR: 表示某一次性错误, 例如某次请求失败. 该错误不会造成服务器整体瘫痪.
>   3. CRITICAL: 表示致死错误, 会导致服务器无法继续运行.

## 3. 使用方法

sample 目录下有 TCP 和 HTTP 的简单使用方法. 当然, 你也可以直接看下面 2 个例子.


### 3.1. TCP 服务器


```Python
import sparrowlet

fd_manager = sparrowlet.FdManager()


class Svr(sparrowlet.TcpServer):

    def on_receive(self, fd):
        fd_manager.send(fd, "hello world!")

    def on_send(self, fd):
        fd_manager.remove(fd)


if __name__ == '__main__':
    port = 8888
    timeout = 10
    tasklet_num = 10
    svr = Svr(port, timeout, tasklet_num)
    # 可以带参数0来自适应开启多进程, 也可以指定进程数
    svr.run(0)
```


### 3.2. HTTP 服务器

```Python
import sparrowlet


class Test(sparrowlet.UriInterface):

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
    svr = sparrowlet.HttpServer(port, timeout, tasklet_num)
    # 注册 URI 的对应逻辑处理类
    uri_dict = {
        '/test': Test
    }
    svr.register(uri_dict)
    # 可以带参数0来自适应开启多进程, 也可以指定进程数
    svr.run()
```
