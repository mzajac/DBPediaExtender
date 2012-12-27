#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import sys
from itertools import izip
from urllib import quote_plus
from math import ceil

from config import results_path, predicates, evaluation_mode, candidates_limit, verbose
from sentence_classifier import get_sentence_classifier, SentenceClassifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor
from evaluator import run_evaluation
from sparql_access import full_predicate_name, full_resource_name

def learn_new_triples(predicate):
    """learns new triples and stores them in a file"""
    sc = get_sentence_classifier(predicate)
    entities = CandidatesSelector.get_candidates(predicate)
    entities = entities[: candidates_limit]
    if verbose:
        print '%s candidates identified' % len(entities)
    n = 10000
    entities_list = [
        entities[i*n : (i+1)*n] 
        for i in xrange(int(ceil(len(entities) / n)))
    ]
    out = open(results_path + 'triples-%s' % predicate, 'w')
    ve = ValueExtractor(predicate, sc.extractor_training_data)
    for entities in entities_list:
        extracted_sentences = sc.extract_sentences(entities)
        values = ve.extract_values(extracted_sentences)
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

