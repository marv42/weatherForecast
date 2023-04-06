import urllib
from urllib import request
from urllib.error import URLError

import PIL
from PIL import Image


# https://docs.python.org/3/howto/descriptor.html#dynamic-lookups
class Cache:

    cache = {}

    def __get__(self, obj, obj_type=None):
        url = str(obj.url)
        try:
            return self.cache[url]
        except KeyError:
            try:
                icon = urllib.request.urlopen(url)
                self.cache[url] = value = PIL.Image.open(icon)
                return value
            except URLError:
                return None
        except TypeError:
            return urllib.request.urlopen(url)


class IconCache:

    get_icon = Cache()

    def __init__(self, url):
        self.url = url
