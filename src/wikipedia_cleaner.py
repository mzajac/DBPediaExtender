#!/usr/bin/env python
# -*- coding: utf-8 -*-

from WikiExtractor import WikiExtractor
from urllib2 import unquote
from collections import namedtuple
from pprint import pprint

def clean(text, we = WikiExtractor()):
    doc = namedtuple('Doc', ['text'])
    doc.text = text
    doc.text = we._WikiExtractor__clean(doc).text
    text = we._WikiExtractor__compact(doc).text
    text = text.encode('utf-8')#.split('\n')
    new = []
    for line in text:
        if line and line[0] not in ['=', ';', '*']:
            new.append(line)
    return unquote(''.join(new))
