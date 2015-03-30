#!/user/bin/env python
# -*- encoding:utf-8 -*-
'''
a simple framework based on epoll
'''
import socket
import select
import errno
import time


class _SocketInfo(object):
    '''_SocketInfo Class

    A structure contains the informations of a socket.

    Attributes:
        __address: The remote IP address.
        __socket: The socket instance.
        __last_access_time: The last access time.
        __send_len: the length of data sent.
        __send_data: the data need to send.
        __recevie_data: the data have received.
    '''

    def __init__(self, address, sock, last_access_time):
        self.__address = address
        self.__socket = sock
        self.__last_access_time = last_access_time
        self.__send_len = 0
        self.__send_data = ''
        self.__receive_data = []

    @property
    def address(self):
        return self.__address

    @property
    def socket(self):
        return self.__socket

    @property
    def last_access_time(self):
        return self.__last_access_time

    @property
    def send_len(self):
        return self.__send_len

    @property
    def send_data(self):
        return self.__send_data

    @property
    def receive_data(self):
        '''Joint the received data.

        Return:
            Return the jointed data.
        '''
        return ''.join(self.__receive_data)

    def set_last_access_time(self, last_access_time):
        self.__last_access_time = last_access_time

    def set_send_data(self, data):
        self.__send_data = data

    def append_data(self, data):
        '''Append the data to the instance.

        Args:
            data: the data needs to append.
        '''
        self.__receive_data.append(data)

    def set_send_len(self, length):
        self.__send_len = length


class _ReceiveComplete(Exception):
    '''_ReceiveComplete Class
    It's an exception for informate the server data have received completly
    '''
    pass


class Server(object):
    '''Server Class
    It contains socket operations (remove, new) and some data operations (send,
    receive).

    Attributes:
        socket_info_dict: The dict for storing fd, socket infomation pairs.
        curr_time: Current access time.
        last_access_time: Last access time.
        listen_fd: The listen socket file descriptor.
        timeout: The time-out time.
        epoll_fd: The epoll file descriptor.
    '''

    MAX_RECV_SIZE = 1024
    HTTP_HEADER_TAG = "Content-Length:"

    def __init__(self, listen_fd, timeout):

        self.socket_info_dict = {}  # {fd: _SocketInfo}
        self.curr_time = time.time()
        self.last_access_time = -1
        self.listen_fd = listen_fd
        self.timeout = timeout
        self.epoll_fd = None

    def remove_socket(self, fd):
        '''Remove a socket from socket_info_dict and unregister it from epoll

        Args:
            fd: A socket file descriptor.
        '''
        try:
            socket_info = self.socket_info_dict[fd]
            self.epoll_fd.unregister(fd)
            socket_info.socket.close()
        except Exception as e:
            pass

        try:
            del self.socket_info_dict[fd]
        except Exception as e:
            pass

    def new_socket(self):
        '''Create a new socket.

        Accept the listen socket, create a new socket and register it in epoll.
        The new socket is a non-blocking socket, we add its information to the
        socket_info_dict.
        '''
        while 1:
            try:
                sock, addr = self.listen_fd.accept()
                sock.setblocking(0)
                self.epoll_fd.register(
                    sock.fileno(),
                    (select.EPOLLIN |
                     select.EPOLLET |
                     select.EPOLLERR |
                     select.EPOLLHUP)
                )
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                socket_info = _SocketInfo(addr, sock, self.curr_time)
                self.socket_info_dict[sock.fileno()] = socket_info
            except socket.error as e:
                break

    def is_complete(self, fd):
        return True
        '''Return the socket's data is complete or not.

        If the content length add header length equals the whole length, the
        data is complete.

        Args:
            fd: A socket file descriptor.

        Return:
            The result of wheather the socket data have received completly.
        '''
        socket_info = self.socket_info_dict.get(fd, None)
        if socket_info is None:
            raise Exception

        data = socket_info.receive_data
        # get content-length
        content_len = 0  # maybe it only has header
        beg_index = data.find(self.__class__.HTTP_HEADER_TAG)
        if beg_index > 0:
            end_index = data.find("\r\n", beg_index)
            if beg_index > 0:
                tag_value = data[
                    beg_index + len(self.__class__.HTTP_HEADER_TAG):
                    end_index
                ].strip()
                if tag_value.isdigit():
                    content_len = int(tag_value)

        if content_len < 0:
            raise Exception

        # get the length of HTTP header
        header_len = 0
        end_index = data.find("\r\n\r\n")
        if end_index > 0:
            header_len = end_index + 4
        else:
            raise Exception

        # get the length of whole-data
        data_len = len(data)

        if content_len + header_len == data_len:
            return True

        return False

    def receive(self, fd):
        '''Receive the data transit through socket.

        Keep receiving data until all data have received, or some error
        occured. Raising an exception while all data have received completly.

        Args:
            fd: the socket file descriptor.

        Raises:
            _ReceiveComplete: The exception means all data have received.
        '''
        socket_info = self.socket_info_dict.get(fd, None)
        if socket_info is None:
            return

        # modify the last access time
        socket_info.set_last_access_time(self.curr_time)
        curr_socket = socket_info.socket

        while 1:
            try:
                data = curr_socket.recv(self.__class__.MAX_RECV_SIZE)
                if data:  # add data
                    socket_info.append_data(data)
                else:  # no data, all datas have been received
                    self.remove_socket(fd)
                    break
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    is_complete = False
                    try:
                        is_complete = self.is_complete(fd)
                    except Exception as e:
                        pass

                    if is_complete:
                        raise _ReceiveComplete
                else:
                    self.remove_socket(fd)
                break

    def send(self, fd):
        '''Send the data through socket.

        Keep sending data untile all data have sent. The send_len denotes the
        length of data sent, send complete when the send_len equals to the data
        length. Removing the socket while all data have sent.

        Args:
            fd: the socket file descriptor.
        '''
        socket_info = self.socket_info_dict.get(fd, None)
        if socket_info is None:
            return

        socket_info.set_last_access_time(self.curr_time)
        curr_socket = socket_info.socket
        send_len = socket_info.send_len
        if len(socket_info.send_data) == 0:
            self.remove_socket(fd)
            return

        while 1:
            try:
                send_len += curr_sock.send(data_for_send[send_len:])
                if send_len == len(socket_info.send_data):  # send complete
                    self.remove_socket(fd)
                    break
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    socket_info.set_send_len(send_len)
                    break
                else:
                    self.remove_socket(fd)

    def check_timeout(self):
        '''Check the timeout status.

        Remove the socket when the socket is timeout. Sync the access time.
        '''
        if self.curr_time - self.last_access_time > self.timeout:
            self.last_access_time = self.curr_time

            for fd, socket_info in self.socket_info_dict.items():
                fd_last_access_time = socket_info.last_access_time
                delta_time = self.curr_time - fd_last_access_time
                if delta_time > self.timeout:
                    self.remove_socket(fd)
                elif fd_last_access_time < self.last_access_time:
                    self.last_access_time = fd_last_access_time

    def init_epoll(self):
        '''Initialize the epoll file descriptor.

        Register the epoll file descriptor.
        '''
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(
                self.listen_fd.fileno(),
                (select.EPOLLIN |
                 select.EPOLLET |
                 select.EPOLLERR |
                 select.EPOLLHUP))
        except select.error as e:
            self.epoll_fd = None

    def epoll_loop(self):
        '''The main loop for this server.

        Get the events, and then new a socket, receive the data, send the data
        or remove the socket. Check the timeout at the last step for remove the
        timeouted socket.
        '''
        if self.epoll_fd is None:
            self.init_epoll()

        while 1:
            epoll_list = self.epoll_fd.poll()

            for fd, events in epoll_list:
                self.curr_time = time.time()
                if fd == self.listen_fd.fileno():
                    self.new_socket()
                elif select.EPOLLIN & events:  # receive
                    try:
                        self.receive(fd)
                    except _ReceiveComplete:
                        # TODO: add your logical task
                        print self.socket_info_dict[fd].receive_data
                elif select.EPOLLHUP & events or select.EPOLLERR & events:
                    self.remove_socket(fd)
                elif select.EPOLLOUT & events:  # send
                    self.send(fd)
                else:
                    continue

                self.check_timeout()
