#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip

from sentence_classifier import get_sentence_classifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor
from evaluator import run_evaluation

def learn_new_triples(predicate):
    """learns new triples and stores them in a file"""
    sc = get_sentence_classifier(predicate)
    entities = CandidatesSelector.get_candidates(predicate)[:100]
    entities, sentences = sc.extract_sentences(entities, verbose=True)
    ve = ValueExtractor(predicate)
    values = [
        ve.extract_value(sentence)
        for entity, sentence in izip(entities, sentences)
    ]
    out = open('triples-%s' % predicate, 'w')
    for e, v in izip(entities, values):
        if v:
            print >>out, '%s %s %s .' % (e, predicate, v)

def main():
    predicates = [
        'populationTotal', 
        'capital', 
        'source', 
        'discharge',
        'areaTotal',
        'mountainRange'
        'elevation'
    ]
    run_evaluation()
#    for p in predicates[0:1]:
#        learn_new_triples(p)
            
if __name__ == '__main__':
    main()

