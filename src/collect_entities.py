from collections import defaultdict

from sparql_access import select_all_entities, select_entities_of_type, full_predicate_name
from config import entities_path
from pickler import Pickler
from language_tools import extract_shortened_name

entities_types = [
    'PopulatedPlace',
    'Settlement',
    'Country',
    'AdministrativeRegion',
    'Atoll',
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

def collect_entities():
    try:
        e = Pickler.load(entities_path)
        return Pickler.load(entities_path)
    except IOError:
        pass
    entities = {}
    for entity in select_all_entities():
        entities[entity] = [] 
    for i, type in enumerate(entities_types):
        entities_of_type = select_entities_of_type(full_predicate_name(type))
        for entity in entities_of_type:
            entities[entity].append(i)
    alternate_names = defaultdict(lambda: [])
    for entity, types in entities.iteritems():
        short = extract_shortened_name(entity)
        if short != entity:
            alternate_names[short] = types
    entities = dict(entities.items() + alternate_names.items())
    Pickler.store(entities, entities_path)
    return entities
    
collect_entities()
