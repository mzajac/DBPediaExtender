
from collections import defaultdict

from sparql_access import select_types, count_entities_of_type

class CandidatesSelector:
    #types that are too wide an cover too many entities
    wide_types = [
        'http://dbpedia.org/ontology/PopulatedPlace',
        'http://schema.org/Place',
        'http://www.w3.org/2002/07/owl#Thing',
        'http://dbpedia.org/ontology/Place',
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
    def select_most_specific_types(predominant_types):
        threshold = 1000
        return [
            type for type in predominant_types
            if count_entities_of_type(type) > threshold
        ]
    
    @staticmethod
    def get_candidates(predicate):
        return CandidatesSelector.select_most_specific_types(CandidatesSelector.get_predominant_types(predicate))
        
if __name__ == '__main__':
    pass
