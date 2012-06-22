#!/usr/bin/env python
import urllib
import json
import sys
from urllib2 import unquote
from collections import defaultdict

data_source = "http://dbpedia.org"
sparql_endpoint = "http://localhost:8890/sparql/"

def full_predicate_name(name):
    return '%s/ontology/%s' % (data_source, name)

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
    
def select_types(predicate):
    query = '''SELECT ?s, ?type FROM <%s> WHERE {
          ?s <%s> ?o.
          ?s rdf:type ?type.
    }''' % (data_source, full_predicate_name(predicate))
    data = get_data(query)['results']['bindings']
    types_dict = defaultdict(list)
    for line in data:
        types_dict[line['s']['value']].append(line['type']['value'])
    return [types for entity, types in types_dict.iteritems()]
    
if __name__ == '__main__':
    pass

