#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip
from urllib import quote_plus

from config import results_path, predicates, evaluation_mode, candidates_limit, verbose
from sentence_classifier import get_sentence_classifier, SentenceClassifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor
from evaluator import run_evaluation
from sparql_access import full_predicate_name, full_resource_name

def learn_new_triples(predicate):
    """learns new triples and stores them in a file"""
    sc = get_sentence_classifier(predicate)
    entities = CandidatesSelector.get_candidates(predicate)[: candidates_limit]
    extracted_sentences = sc.extract_sentences(entities)
    ve = ValueExtractor(predicate, sc.extractor_training_data, sc.most_informative_features)
    values = ve.extract_values(extracted_sentences)
    out = open(results_path + 'triples-%s' % predicate, 'w')
    for e, v in values.iteritems():
        if v:
            print >>out, '<%s> <%s> "%s"@pl .' % (
                full_resource_name(quote_plus(e)).encode('utf-8'), 
                full_predicate_name(predicate).encode('utf-8'), 
                v
            )

def main():    
    for p in predicates:
        if evaluation_mode == 1:
            run_evaluation(p)
        else:
            learn_new_triples(p)
            
if __name__ == '__main__':
    main()

