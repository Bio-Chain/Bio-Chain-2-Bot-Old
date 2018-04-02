import time
from file_string import FileString

TOKEN = ""
END_NODE = '16507419'
CHAT_ID = -1001180504638
LAST_PIN = FileString('last_pin.txt')
BULLET = '. '
BULLET_2 = '  - '


def get_current_timestamp():
    return round(time.time())


def get_html_mention(user_id, text):
    return '<a href="tg://user?id={}">{}</a>'.format(user_id, html_escape(text))


def html_escape(s):    
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def caseless_set_eq(list1, list2):
    return {v.lower() for v in list1} == {v.lower() for v in list2}


def join_with_conjunction(l, sep=', ', conjunction=' and '):
    return sep.join(l[:-2] + [conjunction.join(l[-2:])])
