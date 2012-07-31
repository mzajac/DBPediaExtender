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

from config import entities_path, raw_articles_path, wikidump_path
from language_tools import extract_shortened_name
from collect_entities import collect_entities

def main():
    entities = collect_entities()
    for f in files(wikidump_path):
        parse(f, entities, raw_articles_path)
            
def files(dirname):
    for root, _, files in os.walk(dirname):
        files = map(lambda f: join(root, f), files)
        for f in files:
            yield f
            
def parse(filename, entities, dirname):
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
    
if __name__ == '__main__':
    main()

