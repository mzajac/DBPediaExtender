#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip

from config import results_path, predicates, evaluation_mode, candidates_limit, verbose
from sentence_classifier import get_sentence_classifier, SentenceClassifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor
from evaluator import run_evaluation

def learn_new_triples(predicate):
    """learns new triples and stores them in a file"""
    sc = get_sentence_classifier(predicate)
    entities = CandidatesSelector.get_candidates(predicate)[: candidates_limit]
    entities, sentences = sc.extract_sentences(entities, verbose=verbose)
    ve = ValueExtractor(predicate, sc.extractor_training_data)
    values = [
        ve.extract_value(sentence)
        for entity, sentence in izip(entities, sentences)
    ]
    out = open(results_path + 'triples-%s' % predicate, 'w')
    for e, v in izip(entities, values):
        if v:
            print >>out, '%s %s %s .' % (e, predicate, v)

def main():    
    for p in predicates:
        if evaluation_mode:
            run_evaluation(p)
        else:
            learn_new_triples(p)
            
if __name__ == '__main__':
    main()

