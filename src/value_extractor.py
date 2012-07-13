import os
import sys

import nltk
from nltk.tag.crf import MalletCRF

from config import java_path, mallet_path, models_cache_path

class ValueExtractor:
    def __init__(self, predicate, training_data):
        self.predicate = predicate
        self.training_data = ValueExtractor.convert_training_data(training_data)[:10]
        self.model_filename = models_cache_path % ('model-%s.crf' % predicate)
        nltk.internals.config_java(java_path)
        nltk.classify.mallet.config_mallet(mallet_path)
        try:
            self.model = MalletCRF(self.model_filename, self.features_collector)            
        except IOError:
            self.train()
        
    @staticmethod
    def convert_training_data(data):
        def sublist_index(lst, sublst):
            n = len(sublst)
            for i in xrange(len(lst) - n + 1):
                if sublst == lst[i : i + n]:
                    return i
            raise IndexError
            
        for sentence, value in data:
            start = sublist_index(sentence, value)
            end = start + len(value)
            for i, word in enumerate(sentence):
                sentence[i] = (sentence[i], str(int(start <= i < end)))
        return map(lambda (s, v): s, data)
        
    @staticmethod
    def features_collector(sentence, i):
        def recent_year(word):
            return alldigits(word) and 1990 <= int(word) <= 2012
            
        def other_year(word):
            return alldigits(word) and 1001 <= int(word) <= 1989
            
        def alldigits(word):
            return all(d.isdigit() for d in word)
            
        word = sentence[i]
        window_size = 3            
        features = {
            'recent_year': recent_year(word),
            'other_year': recent_year(word),
            'alldigits': alldigits(word),
#                'common_name': ,
        }
        for j in xrange(-window_size, window_size + 1):
            if 0 <= i + j < len(sentence):
                features['%d' % j] = sentence[i + j]
        return features
        
    def train(self):
        self.model = MalletCRF.train(self.features_collector, self.training_data, self.model_filename)

    def extract_value(self, sentence):
        tagged_sentence = self.model.tag(sentence)
        #TODO check for consecutiveness
        value = ' '.join([
            w for w, tag in tagged_sentence if tag == '1'
        ])
        return value
            
        
        
