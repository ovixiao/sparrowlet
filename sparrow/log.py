import logging
import os

init_flag = False
path = 'log'
filename = 'sparrow.log'


def get_logger():
    global init_flag
    if init_flag:
        return logging.getLogger()
    else:
        init_logger()
        return logging.getLogger()


def init_logger():
    global path, filename, init_flag
    fmt = '%(levelname)s %(asctime)s %(filename)s|%(lineno)d %(message)s'
    formatter = logging.Formatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_path = '{}/{}'.format(path, filename)
    if not os.path.exists(path):
        os.mkdir(path)
    fh = logging.FileHandler(file_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    init_flag = True
