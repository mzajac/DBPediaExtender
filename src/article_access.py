#!/usr/bin/env python
import sys
import os
import glob
from os.path import join
from codecs import open as copen

from wikipedia_cleaner import clean
from config import raw_articles_path, articles_cache_path
from language_tools import LanguageToolsFactory
from pickler import Pickler

lt = LanguageToolsFactory.get_language_tools()

class ArticleNotFoundError(BaseException):
    pass

def get_raw_article(name):
    try:
        f = copen(join(raw_articles_path, name), encoding='utf-8')
        return clean(f.read())
    except IOError:
        raise ArticleNotFoundError(name)

def get_article(name):
    try:
        return Pickler.load(articles_cache_path % name)
    except IOError:
        raise ArticleNotFoundError(name)
        
def prepare_articles(names):
    '''saves tagged articles about given entities in a cache'''
    raw_articles = []
    #save articles in temporary files
    found = False
    for i, name in enumerate(names):
        try:
            get_article(name)
        except ArticleNotFoundError:
            try:
                article = get_raw_article(name).decode('utf-8')
            except ArticleNotFoundError:
                continue
            found = True
            out = copen(join(raw_articles_path, '%d.txt' % i), 'w', 'utf-8')
            print >>out, article
    if found:
        articles = lt.run_tagger()
        #remove temporary files
        for f in glob.glob(join(raw_articles_path, "*.txt*")):
            os.remove(f)
        #save processed articles
        for i, article in articles.iteritems():
            Pickler.store(article, articles_cache_path % names[i])

