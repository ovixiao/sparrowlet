# Sparrow (麻雀)
一个简单又实用的 TCP 服务器, 主要是基于 epoll 进行 IO select, 所以最好还是在 linux 上进行.
其余基于 poll 的纯粹是为了能在 mac 上能调试.


## 1. 依赖

1. 为了提高运行效率, 使用 (stackless python)[http://www.stackless.com/] 来做 "多线程".
