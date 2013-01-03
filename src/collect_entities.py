# -*- coding: utf-8 -*-
import urllib
import urllib2
import itertools
import time
import sys
import json
from collections import defaultdict
from urllib2 import urlopen, Request, unquote

from sparql_access import full_type_name, select_entities_of_type
from config import entities_path
from pickler import Pickler
from config import data_source, sparql_endpoint

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
    'Mountain'
]

def collect_entities():
    try:
        return Pickler.load(entities_path)
    except IOError:
        pass
    entities = defaultdict(list)
    for i, type in enumerate(entities_types):
        entities_of_type = select_entities_of_type(full_type_name(type))
        for entity in entities_of_type:
            entities[entity].append(i)
    Pickler.store(entities, entities_path)
    return entities
    
