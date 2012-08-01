import os
import sys

import nltk
from nltk.tag.crf import MalletCRF

from config import lang, java_path, mallet_path, models_cache_path
from language_tools import LanguageToolsFactory
from collect_entities import entities_types

lt = LanguageToolsFactory.get_language_tools(lang)

class ValueExtractor:
    def __init__(self, predicate, training_data):
        self.predicate = predicate
        self.training_data = ValueExtractor.convert_training_data(training_data)
        self.model_filename = models_cache_path % ('model-%s.crf' % predicate)
        nltk.internals.config_java(java_path)
        nltk.classify.mallet.config_mallet(mallet_path)
        try:
            self.model = MalletCRF(self.model_filename, self.features_collector)            
        except IOError:
            self.train()
        
    @staticmethod
    def convert_training_data(data):
        for sentence, value in data:
            index = sentence.index(value)
            for i, word in enumerate(sentence):
                sentence[i] = (sentence[i], str(int(i == index)))
        return map(lambda (s, v): s, data)
        
    @staticmethod
    def features_collector(sentence, i):
        def recent_year(word):
            try:
                return 1990 <= int(word) <= 2012
            except ValueError:
                return False
            
        def other_year(word):
            try:
                return 1001 <= int(word) <= 1989
            except ValueError:
                return False
            
        def alldigits(word):
            return all(d.isdigit() for d in word)
            
        def is_numeric(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
                
        def normalize(word):
            return ''.join([
                ('0' if char.isdigit() else 
                 'a' if char.islower() else
                 'A' if char.isupper() else
                 ' ' if char == ' ' else
                 '!')
                for char in word    
            ])
            
        sentence = map(lambda w: w.decode('utf-8'), sentence)
        features = {
            'position': i,
        }
        window_size = 3
        for j in xrange(-window_size, window_size + 1):
            if 0 <= i + j < len(sentence):
                word = sentence[i + j]
                is_entity = lt.is_entity(word)
                word_features = {
                    'token': word,
                    'lemma': lt.lemmatize([word.lower()])[0],
                    'recent_year': recent_year(word),
                    'other_year': other_year(word),
                    'alldigits': alldigits(word),
                    'allalpha': all(d.isalpha() or d == ' ' for d in word),
                    'allcapitals': all(d.isupper() for d in word),
                    'starts_with_capital': all(segment.isupper() for segment in word.split()),
                    'numeric': is_numeric(word),
                    'normalized': normalize(word),
                    'entity': is_entity,
                }
                if j == 0:
                    for k in xrange(len(entities_types)):
                        features['type %d' % k] = is_entity and k in lt.entities[word]
                for name, feature in word_features.iteritems():
                    features['%d %s' % (j, name)] = feature
        return features
        
    def train(self):
        self.model = MalletCRF.train(self.features_collector, self.training_data, self.model_filename, trace=0)

    def extract_value(self, sentence):
        tagged_sentence = self.model.tag(sentence)
        values = [
            segment
            for segment, tag in tagged_sentence
            if tag == '1'
        ]
        if len(values) >= 1:
            return values[0]
                   
