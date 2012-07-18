import os
import sys

import nltk
from nltk.tag.crf import MalletCRF

from config import lang, java_path, mallet_path, models_cache_path
from language_tools import LanguageToolsFactory

lt = LanguageToolsFactory.get_language_tools(lang)

class ValueExtractor:
    def __init__(self, predicate, training_data):
        self.predicate = predicate
        self.training_data = ValueExtractor.convert_training_data(training_data)
        for i, _ in enumerate(self.training_data):
            ValueExtractor.store_anchors_tagged(self.training_data[i])
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
    def store_anchors_tagged(sentence):
        for i, (segment, tag) in enumerate(sentence):
            sentence[i] = ((segment, segment.is_anchor), tag)
            
    @staticmethod
    def store_anchors_untagged(sentence):
        for i, segment in enumerate(sentence):
            sentence[i] = (segment, segment.is_anchor)
            
    @staticmethod
    def remove_anchors_tagged(sentence):
        for i, ((segment, anchor), tag) in enumerate(sentence):
            sentence[i] = (segment, tag)
        
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
            
        sentence = map(lambda (w, _): (w.decode('utf-8'), _), sentence)
        features = {}
        window_size = 5
        for j in xrange(-window_size, window_size + 1):
            if 0 <= i + j < len(sentence):
                word, is_anchor = sentence[i + j]
                word_features = {
                    'token': word,
                    'lemma': lt.lemmatize([word.lower()])[0],
                    'position': i,
                    'recent_year': recent_year(word),
                    'other_year': other_year(word),
                    'alldigits': alldigits(word),
                    'allalpha': all(d.isalpha() for d in word),
                    'allcapitals': all(d.isupper() for d in word),
                    'starts_with_capital': word[0].isupper(),
                    'numeric': is_numeric(word),
                    'is_anchor': is_anchor,
                }
                for name, feature in word_features.iteritems():
                    features['%d %s' % (j, name)] = feature
        return features
        
    def train(self):
        self.model = MalletCRF.train(self.features_collector, self.training_data, self.model_filename)

    def extract_value(self, sentence):
        sentence_with_anchors = sentence[:]
        ValueExtractor.store_anchors_untagged(sentence_with_anchors)
        tagged_sentence = self.model.tag(sentence_with_anchors)
        ValueExtractor.remove_anchors_tagged(tagged_sentence)
        values = []
        value = []
        for w, tag in tagged_sentence:
            if tag == '1':
                value.append(w)
            elif value:
                values.append(' '.join(value))
                value = []
        if value:
            values.append(' '.join(value))
        if len(values) >= 1:
            return values[0]
                   
