#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from WikiExtractor import WikiExtractor
from urllib2 import unquote
from collections import namedtuple
from pprint import pprint

def clean(text, we = WikiExtractor()):
    doc = namedtuple('Doc', ['text'])
    doc.text = text
    doc.text = we._WikiExtractor__clean(doc).text
    text = we._WikiExtractor__compact(doc).text
    text = text.encode('utf-8')
    link_dictionary = doc.link_dictionary
    new = []
    for line in text:
        if line and line[0] not in ['=', ';', '*']:
            line = line.replace('()', '')
            new.append(line)
    return unquote(''.join(new)).decode('utf-8'), link_dictionary
   
