import urllib
from urllib import request


# https://docs.python.org/3/howto/descriptor.html#dynamic-lookups
class Cache:

    cache = {}

    def __get__(self, obj, obj_type=None):
        url = str(obj.url)
        try:
            return self.cache[url]
        except KeyError:
            self.cache[url] = value = urllib.request.urlopen(url)
            return value
        except TypeError:
            return urllib.request.urlopen(url)


class IconCache:

    get_icon = Cache()

    def __init__(self, url):
        self.url = url
