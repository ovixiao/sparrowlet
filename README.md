# sparrow
一个简单又实用的 TCP 服务器, 由于是基于 epoll 进行 IO select, 所以暂时只能运行在
linux 上.

## 1. 依赖

1. 为了提高运行效率, 使用 (stackless python)[http://www.stackless.com/] 来做 "多线程".
