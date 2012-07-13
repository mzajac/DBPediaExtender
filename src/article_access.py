#!/usr/bin/env python
import sys
from os.path import join
from codecs import open as copen

from wikipedia_cleaner import clean
from config import raw_articles_path

class ArticleNotFoundError(BaseException):
    pass

def get_article(name):
    try:
        f = copen(join(raw_articles_path, name), encoding='utf-8')
        return clean(f.read())
    except IOError:
        raise ArticleNotFoundError(name)
