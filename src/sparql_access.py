#!/usr/bin/env python
import urllib
import json
import sys
from urllib2 import unquote

data_source = "http://dbpedia.org"
sparql_endpoint = "http://localhost:8890/sparql/"

def full_predicate_name(name):
    return 'http://dbpedia.org/ontology/%s' % name

def strip_url_prefix(s):
    return s[28:]

def get_data(query):
    params = {
    	"query": query,
    	"format": "application/json"
    }
    request = urllib.urlencode(params)
    response = urllib.urlopen(sparql_endpoint, request).read()
    return json.loads(response)
	
def select_all(d):
    dd = {}
    for c in ['s', 'p', 'o']:
        if c not in d:
            dd[c] = '?%c' % c
        else:
            dd[c] = '<' + d[c] + '>' if c != 'p' else '<' + full_predicate_name(d[c]) + '>'
    query = 'SELECT * FROM <%s> WHERE {%s %s %s}' % (data_source, dd['s'], dd['p'], dd['o'])
    data = get_data(query)['results']['bindings']
    ret = []
    for line in data:
        t = []
        for c in ['s', 'p', 'o']:
            if c in line:
                value = line[c]['value']
                if value.startswith('%s/resource/' % data_source):
                    value = strip_url_prefix(value)
                value = unquote(value.encode('utf-8'))
                t.append(value)
        ret.append(tuple(t))
    return ret
    
if __name__ == '__main__':
    query = 'SELECT * FROM <%s> WHERE {?s ?p ?o}' % data_source   
    data = get_data(query)

