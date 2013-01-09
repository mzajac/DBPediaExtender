# -*- coding: utf-8 -*-

from __future__ import division
import sys
from itertools import izip
from os.path import join
import pylab as pl

from config import tests_path, verbose
from sentence_classifier import get_sentence_classifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor
from sparql_access import select_all

class Stats:
    def __init__(self, tp, fp, fn):
        self.tp, self.fp, self.fn = tp, fp, fn
        
    def __repr__(self):
        self.calculate_statistics()
        return 'precision:%.2f recall:%.2f F-measure:%.2f all:%d' % (self.precision, self.recall, self.f_measure, self.tp + self.fn)

    def calculate_statistics(self):
        self.precision = self.tp / max(self.tp + self.fp, 1)
        self.recall = self.tp / max(self.tp + self.fn, 1)
        self.f_measure = 2 * self.precision * self.recall / (self.precision + self.recall) if self.precision != 0 else 0
        
class Evaluator:
    @classmethod
    def evaluate(cls, true_values, values):
        tp, fp, fn = cls.classify_by_error_type(true_values, values)
        s = Stats(len(tp), len(fp), len(fn))
        print s
        return s, fp, fn
    
    @classmethod
    def classify_by_error_type(cls, true_values, suggested_values):
        tp, fp, fn = [], [], []
        for entity, suggested_value in suggested_values.iteritems():
            if not suggested_value:
                continue
            if entity in true_values and cls.value_matches(true_values[entity], suggested_value):
                tp.append(entity)
            else:
                fp.append(entity)
        for entity, true_value in true_values.iteritems():
            if not suggested_values.get(entity) or not cls.value_matches(true_value, suggested_values[entity]):
                fn.append(entity)
        return tp, fp, fn
        
class ValueExtractorEvaluator(Evaluator):
    @staticmethod
    def value_matches(true_values, suggested_value):
        return any(
            v == suggested_value
            for v in true_values    
        )

def get_test_data(predicate):
    entities = open(join(tests_path, predicate, 'entities')).read().split()
    values = open(join(tests_path, predicate, 'values')).read().split('\n')
    true_values = {}
    for value in values:
        value = value.split()
        if value:
            true_values[value[0]] = value[1:]
    return entities, true_values
      
def run_evaluation(predicate, sentence_limit=None):
    entities, true_values = get_test_data(predicate)
    sc = get_sentence_classifier(predicate, sentence_limit)
    true_values = dict((k, v) for k, v in true_values.iteritems() if k in entities)
    if verbose:
        print '%d entities were used in evaluation.' % len(entities)
    extracted_sentences = sc.extract_sentences(entities)
    ve = ValueExtractor(predicate, sc.extractor_training_data)
    values = ve.extract_values(extracted_sentences)
    print '%s results:' % predicate
    stats, fp, fn = ValueExtractorEvaluator.evaluate(true_values, values)
    table_format = '%30s %30s %20s %10s'
    print 'Error table:'
    print table_format % ('Subject:', 'Gold standard values:', 'Extracted value:', 'Error:')
    for entity, value in values.iteritems():
        if entity not in true_values:
            true_values[entity] = '-'
    for entity, true_value in true_values.iteritems():
        if entity in fp and entity in fn:
            err = 'FP/FN'
        elif entity in fp:
            err = 'FP'
        elif entity in fn:
            err = 'FN'
        else:
            err = ''
        print table_format % (entity[:30], ', '.join(true_value), values[entity] if entity in values else '-', err)
    print '\n\n'
    return stats
    
def incremental_evaluation(predicate):
    from collections import defaultdict
    precision = defaultdict(int)
    recall = defaultdict(int)
    n = 10
    x = [10, 25, 50, 100, 250, 500, 1000, 2500]
    for _ in xrange(n):
        for limit in x:
            s = run_evaluation(predicate, limit)
            precision[limit] += s.precision
            recall[limit] += s.recall
    precision = [v/n for _, v in sorted(list(precision.iteritems()))]
    recall = [v/n for _, v in sorted(list(recall.iteritems()))]
    print precision
    print recall    
        
