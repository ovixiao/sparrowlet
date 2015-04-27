import collections
import protocol.sushi


class Task(object):

    def __init__(self, fd, data, disconnected=False):
        self.__fd = fd
        self.__data = [data]
        self.__disconnnect = False

    def append(self, data):
        self.__data.append(data)

    def disconnect(self):
        self.__disconnect = True

    def check(self):
        print self.data

    @property
    def data(self):
        if len(self.__data) > 1:
            self.__data = [''.join(self.__data)]
        return self.__data[0]

    @property
    def fd(self):
        return self.__fd


class Manager(object):

    def __init__(self):
        self.__tasks = {}

    def add(self, fd, data):
        if fd in self.__tasks:
            self.__tasks[fd].append(data)
        else:
            self.__tasks[fd] = Task(fd, data)

        self.check(fd)

    def check(self, fd):
        task = self.__tasks.get(fd, None)
        if task:
            task.check()

    def disconnect(self, fd):
        task = self.__tasks.get(fd, None)
        if task:
            task.disconnect()


if __name__ == '__main__':
    manager = Manager()
    manager.add(4, 'hello')
    manager.add(4, 'world')
