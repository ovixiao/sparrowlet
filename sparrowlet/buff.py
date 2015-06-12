#!/user/bin/env python
# -*- encoding:utf-8 -*-


class Buff(list):
    '''Buff 缓冲类
    旨在提高字符串处理的效率, 因为现实中会出现较多的 append 零碎数据场景
    而 Python 的字符串修改操作是十分费时的.
    '''

    def __init__(self, init_str=None, *args, **kargs):
        '''初始化

        参数:
            init_str: 初始化时使用的字符串
        '''
        list.__init__(self, *args, **kargs)
        if init_str is not None:
            self.append(init_str)

    def append(self, string):
        '''如果 string 是 unicode string, 那么 append 进去的就是 unicode 字符
        请不要混合使用, 免得出错. 这里没有加入判断是为了提高运行效率.
        '''
        list.append(self, string)

    def pop_str(self):
        '''返回数据结果, 因为数据拼接效率很低, 所以需要使用时才会拼接
        注意, 调用过该函数后数据会清空
        '''
        data = ''.join(self)
        self.clean()
        return data

    def clean(self):
        '''清空数组
        '''
        del self[:]
