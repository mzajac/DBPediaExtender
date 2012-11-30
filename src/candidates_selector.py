#encoding: utf-8
from collections import defaultdict

from config import candidates_cache_path
from sparql_access import select_types, count_entities_of_type, select_entities_of_type_not_in_relation
from pickler import Pickler

class CandidatesSelector:
    #types that are too wide, cover too many entities and should never be returned
    wide_types = [
        'http://schema.org/Place',
        'http://www.w3.org/2002/07/owl#Thing',
        'http://dbpedia.org/ontology/Place',
        'http://dbpedia.org/ontology/NaturalPlace',
        'http://dbpedia.org/ontology/BodyOfWater',
        'http://www.opengis.net/gml/_Feature'
    ]

    @staticmethod
    def get_predominant_types(predicate, subject=True):
        type_preciseness = .9
        types_list = select_types(predicate, subject)
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
        threshold = 100
        return [
            type for type in predominant_types
            if count_entities_of_type(type) > threshold
        ]
    
    @staticmethod
    def get_candidates(predicate):
        try:
            return Pickler.load(candidates_cache_path % predicate)
        except IOError:
            pass
        types = CandidatesSelector.get_most_specific_types(
            CandidatesSelector.get_predominant_types(predicate)
        )
        if types: 
            print types
            candidates = select_entities_of_type_not_in_relation(
                types[0], 
                predicate
            )
            Pickler.store(candidates, candidates_cache_path % predicate)
            return candidates
        else:
            return []
        
