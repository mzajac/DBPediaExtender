#encoding: utf-8
import sys
from collections import defaultdict

from config import candidates_cache_path, type_restrictions
from sparql_access import select_types, count_entities_of_type, select_entities_of_type_not_in_relation, full_type_name
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
        if predicate in type_restrictions:
            return [full_type_name(type_restrictions[predicate])]
        #limiting these relations to settlements only increases precision a lot
        if predicate in ['stolica', 'gmina', 'region', 'prowincja', 'hrabstwo']:
            return [u'http://dbpedia.org/ontology/Settlement']
        type_preciseness = .75
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
            candidates = select_entities_of_type_not_in_relation(
                types[0], 
                predicate
            )
            if predicate == 'gmina':
                candidates = filter(lambda e: 'Gmina' not in e, candidates)
            if predicate == 'powiat':
                candidates = filter(lambda e: 'Powiat' not in e, candidates)
            if predicate == 'hrabstwo':
                candidates = filter(lambda e: 'hrabstwo_miejskie' not in e and 'Hrabstwo' not in e, candidates)
            Pickler.store(candidates, candidates_cache_path % predicate)
            return candidates
        else:
            return []

