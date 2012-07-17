# -*- coding: utf-8 -*-

from __future__ import division
from itertools import izip
from os.path import join

from config import tests_path
from sentence_classifier import get_sentence_classifier
from candidates_selector import CandidatesSelector
from value_extractor import ValueExtractor

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
    def evaluate(cls, true_values, entities, values, verbose=False):
        tp, fp, fn = cls.classify_by_error_type(true_values, entities, values)
        print Stats(len(tp), len(fp), len(fn))
        print 'True positives:'
        print tp
        print 'False positives:'
        print fp
        print 'False negatives:'
        print fn
        print
    
    @classmethod
    def classify_by_error_type(cls, true_values, entities, values):
        tp, fp, fn = [], [], []
        suggested_values = dict(zip(entities, values))
        for entity, value in suggested_values.iteritems():
            if not value:
                continue
            if entity in true_values and cls.value_matches(true_values, value, entity):
                tp.append(entity)
            else:
                fp.append(entity)
        for entity, value in true_values.iteritems():
            if not suggested_values.get(entity) or not cls.value_matches(suggested_values, value[0], entity):
                fn.append(entity)
        return tp, fp, fn
        
class SentenceClassifierEvaluator(Evaluator):
    @staticmethod
    def value_matches(values, value, entity):
        return any(str(v) in value for v in values[entity])
        
class ValueExtractorEvaluator(Evaluator):
    @staticmethod
    def value_matches(values, value, entity):
        if type(values[entity]) != list:
            values[entity] = [values[entity]]
        return any(str(v) == value for v in values[entity])
                
                    
def get_test_data(predicate):
    entities = open(join(tests_path, predicate, 'entities')).read().split()
    values = open(join(tests_path, predicate, 'values')).read().split('\n')
    true_values = {}
    for value in values:
        value = value.split()
        if value:
            true_values[value[0]] = value[1:]
    return entities, true_values  
      
def run_evaluation(predicate):
    entities, true_values = get_test_data(predicate)
    sc = get_sentence_classifier(predicate)
    entities, sentences = sc.extract_sentences(entities, verbose=False)
    ve = ValueExtractor(predicate, sc.extractor_training_data)
    values = [
        ve.extract_value(sentence)
        for entity, sentence in izip(entities, sentences)
    ]
    _, _, false_negatives = SentenceClassifierEvaluator.classify_by_error_type(true_values, entities, sentences)
    print 'Sentence classifier:'
    SentenceClassifierEvaluator.evaluate(true_values, entities, sentences)
    true_values_without_entities_excluded = {}
    for entity, value in true_values.iteritems():
        if entity not in false_negatives:
            true_values_without_entities_excluded[entity] = value
    print 'Value extractor classifier:'
    ValueExtractorEvaluator.evaluate(true_values_without_entities_excluded, entities, values)
    print 'Overall:'
    ValueExtractorEvaluator.evaluate(true_values, entities, values)

