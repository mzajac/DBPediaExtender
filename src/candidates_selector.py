
from collections import defaultdict

from sparql_access import select_types

class CandidatesSelector:
    @staticmethod
    def get_predominant_types(predicate):
        type_preciseness = .9
        types_list = select_types(predicate)
        types_count = defaultdict(int)
        for types in types_list:
            for type in types:
                types_count[type] += 1
        num_entities = len(types_list)
        return [
            type for type, count in types_count.iteritems()
            if count >= type_preciseness * num_entities
        ]
        
    @staticmethod
    def select_most_specific_types(predominant_types):
        return predominant_types
    
    @staticmethod
    def get_candidates(predicate):
        types = CandidatesSelector.select_most_specific_types(CandidatesSelector.get_predominant_types(predicate))
        print types
        
if __name__ == '__main__':
    CandidatesSelector.get_candidates('capital')
