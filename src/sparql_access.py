#!/usr/bin/env python
import urllib
import json
import sys
from urllib2 import unquote
from collections import defaultdict

from config import data_source, sparql_endpoint

def full_predicate_name(name):
    if name in ['completionDate']:
        return '%s/property/%s' % (data_source, name)
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
    
def get_results(query):
    data = get_data(query)['results']['bindings']
    return [
        unquote(strip_url_prefix(line['s']['value']).encode('utf-8'))
        for line in data
    ]     
    
def get_pairs(query):
    data = get_data(query)['results']['bindings']
    return [
        (unquote(strip_url_prefix(line['s']['value']).encode('utf-8')), line['o']['value'])
        for line in data
    ]     
	
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
    
def count_entities_of_type(type):
    query = '''SELECT count(*) FROM <%s> WHERE {
        ?s a <%s>.
    }''' % (data_source, type)
    return int(get_data(query)['results']['bindings'][0]['callret-0']['value'])
    
def select_entities_of_type(type):
    query = '''SELECT * FROM <%s> WHERE {
        ?s a <%s>.
    }''' % (data_source, type)
    return get_results(query)
    
def select_entities_of_types_not_in_relation(types, predicate):
    query = [
        '''PREFIX dbpedia-owl: <%s/ontology/>
           SELECT ?s FROM <%s> WHERE {
               ?s rdf:type ?type
               OPTIONAL {
                   ?s dbpedia-owl:%s ?p.
               }
               FILTER (!bound(?p))
               FILTER (
        ''' % (data_source, data_source, predicate)
    ]
    subquery = []
    for type in types:
        subquery.append('?type = <%s>' % type)
    query.append(' || '.join(subquery))
    query.append(')}')
    query = '\n'.join(query)
    return get_results(query)
    
def select_entities_of_type_in_relation(type, predicate):
    query = '''SELECT ?s, ?o FROM <%s> WHERE {
        ?s a <%s>.
        ?s <%s> ?o.
    }''' % (data_source, full_predicate_name(type), full_predicate_name(predicate))
    return get_pairs(query)
    
def select_all_entities():
    query = '''SELECT DISTINCT ?s FROM <%s> WHERE {
      ?s ?p ?o.
    }''' % data_source
    return get_results(query)
    
if __name__ == '__main__':
    pass

