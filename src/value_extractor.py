import os
import sys
import nltk
from nltk.tag.crf import MalletCRF

from config import java_path, mallet_path, models_cache_path, verbose, numeric_predicates
from language_tools import LanguageToolsFactory, is_numeric
from collect_entities import entities_types
from candidates_selector import CandidatesSelector

lt = LanguageToolsFactory.get_language_tools()

class ValueExtractor:
    def __init__(self, predicate, training_data, features):
        self.predicate = predicate
        self.training_data = ValueExtractor.convert_training_data(training_data)
        #most_informative_features are global, because features_collector cannot take any parameters and must be static
        global most_informative_features  
        most_informative_features = features
        self.predominant_types = map(
            lambda t: t.split('/')[-1], 
            CandidatesSelector.get_predominant_types(predicate, False)
        )
        print self.predominant_types
        nltk.internals.config_java(java_path)
        nltk.classify.mallet.config_mallet(mallet_path)
        self.train()
        
    @staticmethod
    def convert_training_data(data):
        for sentence, value in data:
            lemmas = [word.lemma for word in sentence]
            tags = [0] * len(sentence)
            for i, lemma in enumerate(lemmas):
                for part in value:
                    if lemma == part:
                        tags[i] = 1
                        break
            for i in xrange(len(sentence)):
                sentence[i] = (sentence[i], str(tags[i]))
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
        
        lemma = sentence[i].lemma
        segment = sentence[i].segment
        lemmas = [word.lemma for word in sentence]
        features = {
            'segment': segment,
            'tag': sentence[i].tag,
            'lemma': lemma,
            'recent_year': recent_year(lemma),
            'other_year': other_year(lemma),
            'alldigits': all(c.isdigit() for c in lemma),
            'allalpha': all(c.isalpha() for c in lemma),
            'allcapitals': all(c.isupper() for c in lemma),
            'starts_with_capital': lemma[0].isupper(),
            'segm_starts_with_capital': segment[0].isupper(),
            'numeric': is_numeric(lemma)
        }
        #note if window before and after contains one of the words deemed significant by the sentence classifier
        window_size = 7
        for feature in most_informative_features:
            features['%s before' % feature] = feature in lemmas[max(0, i-window_size): i]
            features['%s after' % feature] = feature in lemmas[i+1: i+1+window_size]
        return features
        
    def train(self):
        self.model = MalletCRF.train(self.features_collector, self.training_data, trace=0)

    def extract_value(self, sentence):
        tagged_sentence = self.model.tag(sentence)
        values = []
        value = []
        for word, tag in tagged_sentence + [('', '0')]:
            if tag == '1':
                value.append(word.lemma)
            else:
                if value:
                    values.append('_'.join(value))
                    value = []
        if values:
            if self.predicate in numeric_predicates:
                return values[0]
            #to increase precision of extraction (at the cost of recall) in textual relations, 
            #only values that are geographic entities in DBPedia are returned
            values_identified_as_entities = [
                v for v in values if lt.is_entity(v)
            ]
            values_identified_as_entities_of_right_type = [
                v for v in values_identified_as_entities if\
                any(entities_types.index(t) in lt.entities[v] for t in self.predominant_types)
            ]
            if verbose:
                print 'Potential values:'
                print ' '.join(values)
                print ' '.join(values_identified_as_entities)
                print ' '.join(values_identified_as_entities_of_right_type)
                print
            if values_identified_as_entities_of_right_type:
                return values_identified_as_entities_of_right_type[0]
#            if values_identified_as_entities:
#                return values_identified_as_entities[0]
                   
