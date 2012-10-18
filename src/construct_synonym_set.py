#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import itertools
import time
import sys
import json
from collections import defaultdict
from urllib2 import urlopen, Request, unquote

from config import synonyms_path, sparql_endpoint
from sparql_access import get_data
from pickler import Pickler

query = '''SELECT * WHERE {
    ?s <http://dbpedia.org/ontology/wikiPageRedirects> ?o .
    ?o a <http://dbpedia.org/ontology/Place> .
}'''

def get_synonyms():
    try:
        return Pickler.load(synonyms_path)
    except IOError:
        pass
    synonyms = defaultdict(list)
    synonyms_and_entities = get_data(query)['results']['bindings']
    for v in synonyms_and_entities:
        synonym = unquote(v['s']['value'].split('/')[-1].encode('utf-8')).replace('_', ' ')
        entity = unquote(v['o']['value'].split('/')[-1].encode('utf-8')).replace('_', ' ')
        if entity not in synonyms[synonym]:
            synonyms[synonym].append(entity)
    Pickler.store(synonyms, synonyms_path)
    return synonyms

if __name__ == '__main__':
    get_synonyms()
