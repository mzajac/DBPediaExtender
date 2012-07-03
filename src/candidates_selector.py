
from collections import defaultdict

from sparql_access import select_types, count_entities_of_type, select_entities_of_types_not_in_relation
from pickler import Pickler

cache_path = '/home/mz/Dokumenty/dbpedia-enricher/cache/candidates/%s'

class CandidatesSelector:
    #types that are too wide and cover too many entities
    wide_types = [
        'http://dbpedia.org/ontology/PopulatedPlace',
        'http://schema.org/Place',
        'http://www.w3.org/2002/07/owl#Thing',
        'http://dbpedia.org/ontology/Place',
        'http://dbpedia.org/ontology/NaturalPlace',
        'http://www.opengis.net/gml/_Feature'
    ]

    @staticmethod
    def get_predominant_types(predicate):
        type_preciseness = .9
        types_list = select_types(predicate)
        types_count = defaultdict(int)
        for types in types_list:
            for type in types:
                if type not in CandidatesSelector.wide_types:
                    types_count[type] += 1
        num_entities = len(types_list)
        return [
            type for type, count in types_count.iteritems()
            if count >= type_preciseness * num_entities
        ]
        
    @staticmethod
    def get_most_specific_types(predominant_types):
        threshold = 1000
        return [
            type for type in predominant_types
            if count_entities_of_type(type) > threshold
        ]
    
    @staticmethod
    def get_candidates(predicate):
        try:
            return Pickler.load(cache_path % predicate)
        except IOError:
            pass
        candidates = select_entities_of_types_not_in_relation(
            CandidatesSelector.get_most_specific_types(
                CandidatesSelector.get_predominant_types(predicate)
            ), 
            predicate
        )
        Pickler.store(candidates, cache_path % predicate)
        return candidates
        
if __name__ == '__main__':
    pass
