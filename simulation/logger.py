'''
Log messages.
'''

from datetime import datetime


def log(time_now, text):
    time_str = datetime.utcfromtimestamp(time_now).strftime(
        '%Y-%m-%d %H:%M:%S')
    print("[%s] %s" % (time_str, text))
