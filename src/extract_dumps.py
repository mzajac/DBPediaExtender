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

def main(dirname, out_dirname, triples_path):
    entities = collect_all_entities(triples_path)
    for f in files(dirname):
        parse(f, entities, out_dirname)
            
def files(dirname):
    for root, _, files in os.walk(dirname):
        files = map(lambda f: join(root, f), files)
        for f in files:
            yield f
            
def collect_all_entities(triples_path):
    filename = 'entities.pkl'
    try:
        return Pickler.load(filename)
    except IOError:
        pass
    s = set()
    for f in files(triples_path):
        f = open(f)
        for line in f:
            name = unquote(line.split()[0][29:-1])
            s.add(name)
    Pickler.store(s, filename)
    return s

def parse(filename, entities, dirname):
    f = BZ2File(filename)
    for _, elem in etree.iterparse(f, events=('end',)):
        if elem.tag[-5:] == 'title':
            name = elem.text.encode('utf-8').replace(' ', '_')
        elif elem.tag[-4:] == 'text':
            if name in entities:
                #some names have slashes in them
                name = name.replace('/', '_')
                out = copen(join(dirname, name), 'w', 'utf-8')
                print >>out, elem.text
                out.close()
        elem.clear()
    f.close()
    
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])

