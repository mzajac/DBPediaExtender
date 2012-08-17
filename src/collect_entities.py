# -*- coding: utf-8 -*-
import urllib
import urllib2
import itertools
import time
import sys
import json
from collections import defaultdict
from urllib2 import urlopen, Request, unquote

from sparql_access import full_predicate_name
from config import entities_path
from pickler import Pickler
from language_tools import extract_shortened_name
from config import data_source

entities_types = [
    'Place',
    'PopulatedPlace',
    'Settlement',
    'Country',
    'AdministrativeRegion',
    'Continent',
    'Island',
    'City',
    'River',
    'BodyOfWater',
    'Stream',
    'Lake',
    'NaturalPlace',
    'MountainRange',
    'Valley',
    'Volcano',
    'Cave',
    'ArchitecturalStructure',
    'Infrastructure',
    'Park',
    'Building',
]

sparql_endpoint = 'http://dbpedia.org/sparql'
limit = 10000

def select_entities_of_type(type):
    entities = []
    for i in itertools.count(0):
        data = get_data(get_query(type, limit, i * limit))['results']['bindings']
        for v in data:
            entity = unquote(v['s']['value'].split('/')[-1].encode('utf-8')).replace('_', ' ')
            entities.append(entity)
        if len(data) < limit:
            break
    return entities
    
def get_query(type, limit, offset):
    return '''SELECT ?s FROM <%s> WHERE {
        ?s a <%s>.
    }
    limit %d
    offset %d''' % (data_source, type, limit, offset)

def get_data(query):
    while True:
        request = Request(sparql_endpoint)
        request.add_header('Accept', 'application/json')
        request.add_data(urllib.urlencode({'query' : query}))
        try:
            return json.loads(urlopen(request).read())
        except urllib2.HTTPError:
            #server blocks us, let's wait a moment
            time.sleep(10)

def collect_entities():
    try:
        print 'Tasman Sea' in Pickler.load(entities_path)
        return Pickler.load(entities_path)
    except IOError:
        pass
    entities = defaultdict(list)
    for i, type in enumerate(entities_types):
        entities_of_type = select_entities_of_type(full_predicate_name(type))
        for entity in entities_of_type:
            entities[entity].append(i)
    Pickler.store(entities, entities_path)
    return entities
    
collect_entities()
