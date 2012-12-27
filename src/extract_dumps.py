#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from urllib2 import unquote
from bz2 import BZ2File
import lxml.etree as etree
from pickler import Pickler
from codecs import open as copen
from os.path import join

from config import entities_path, raw_articles_path, wikidump_path, articles_url
from collect_entities import collect_entities

def main():
    entities = collect_entities()
    parse(join(wikidump_path, articles_url.split('/')[-1]), entities, raw_articles_path)
            
def parse(filename, entities, dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    f = BZ2File(filename)
    for _, elem in etree.iterparse(f, events=('end',)):
        if elem.tag[-5:] == 'title':
            name = elem.text.encode('utf-8').replace(' ', '_')
        elif elem.tag[-4:] == 'text':
            if name in entities:
                #some names have slashes in them
                name = name.replace('/', '_').replace(' ', '_')
                out = copen(join(dirname, name), 'w', 'utf-8')
                print >>out, elem.text
                out.close()
        elem.clear()
    f.close()
    
