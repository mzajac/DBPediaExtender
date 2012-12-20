#encoding: utf-8
import os
import sys
from codecs import open as copen
from subprocess import Popen, PIPE
from itertools import izip
from locale import atof
from urllib import quote_plus

from config import models_cache_path, verbose, numeric_predicates, use_parser, evaluation_mode
from language_tools import LanguageToolsFactory, is_numeric
from collect_entities import entities_types
from candidates_selector import CandidatesSelector

lt = LanguageToolsFactory.get_language_tools()

class ValueExtractor:
    def __init__(self, predicate, training_data):
        self.predicate = predicate
        self.predominant_types = map(
            lambda t: t.split('/')[-1], 
            CandidatesSelector.get_predominant_types(predicate, False)
        )
        self.model_filename = 'crfmodel'
        self.features_train_filename = 'features_train'
        self.features_tag_filename = 'features_tag'
        self.train(training_data)
        
    def extract_features(self, sentence, i, window_size=3):
        def recent_year(word):
            try:
                return 1990 <= int(word) <= 2012
            except ValueError:
                return False
        
        features = {}
        for j in xrange(-window_size, window_size + 1):
            if 0 <= i + j < len(sentence):
                word = sentence[i + j]
                lemma = word.lemma
                if is_numeric(lemma):
                    lemma = str(int(atof(lemma)))
                segment = word.segment
                tag = word.tag
                word_features = {
                    'segment': segment,
                    'tag': lt.get_tag(tag),
                    'case': lt.get_case(tag),
                    'number': lt.get_number(tag),
                    'gender': lt.get_gender(tag),
                    'person': lt.get_person(tag),
                    'aspect': lt.get_aspect(tag),
                    'lemma': lemma,
                    'recent_year': str(int(recent_year(lemma))),
                    'alldigits': str(int(lemma.isdigit())),
                    'allalpha': str(int(lemma.decode('utf-8').isalpha())),
                    'starts_with_capital': str(int(lemma.decode('utf-8')[0].isupper())),
                    'segm_starts_with_capital': str(int(segment.decode('utf-8')[0].isupper())),
                    'numeric': str(int(is_numeric(lemma)))
                }
                if use_parser:
                    word_features['parse'] = word.parse
                for name, feature in word_features.iteritems():
                    features['%d%s' % (j, name)] = feature
        return features
        
    def save_features_to_file(self, filename, sentences, selected_values=None):
        f = copen(models_cache_path % filename, 'w', 'utf-8')
        for i, sentence in enumerate(sentences):
            for j, word in enumerate(sentence):
                if selected_values:
                    values = selected_values[i]
                    cls = int(any(value.lower() in [word.lemma.lower(), word.segment.lower()] for value in values))
                    print >>f, '%d\t' % cls,
                for name, value in self.extract_features(sentence, j).iteritems():
                    print >>f, ('%s=%s\t' % (name, value)).decode('utf-8'),
                print >>f
            print >>f
        
    def train(self, training_data):
        sentences, selected_values = zip(*training_data)
        self.save_features_to_file(self.features_train_filename, sentences, selected_values)
        command = 'crfsuite learn -m %s %s' % (models_cache_path % self.model_filename, models_cache_path % self.features_train_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        p.communicate()
        if verbose:
            self.print_most_informative_features()
        
    def print_most_informative_features(self, n=50):
        command = 'crfsuite dump %s' % (models_cache_path % self.model_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate()
        out = out.split('\n')[:-3]
        start = out.index('STATE_FEATURES = {')
        feature_weights = []
        for line in out[start+1 :]:
            _, feature, __, cls, weight = filter(lambda _: _, line.split(' '))
            cls = cls[0]
            if cls == '1':
                weight = float(weight)
                feature_weights.append((weight, feature))
        feature_weights.sort(key=lambda (w, _): -w)
        feature_weights = filter(lambda (w, _): 1, feature_weights[:n])
        print 'Value extractor - most informative features:'
        for weight, feature in feature_weights:
            print '%s %s' % (weight, feature)
        print

    def extract_values(self, extracted_sentences, confidence_level=.7):
        sentences = [
            sentence
            for entity, sentences in extracted_sentences.iteritems()
            for sentence in sentences
        ]
        self.save_features_to_file(self.features_tag_filename, sentences)
        command = 'crfsuite tag -i -m %s %s' % (models_cache_path % self.model_filename, models_cache_path % self.features_tag_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate()
        tags_list = []
        tags = []
        for line in out.split('\n')[:-1]:
            if not line:
                tags_list.append(tags)
                tags = []
            else:
                tags.append((line[0], float(line[2:])))
        extracted_values = {}
        i = 0
        for entity, sentences in extracted_sentences.iteritems():
            values = []
            for sentence in sentences:
                tags = tags_list[i]
                i += 1
                value = []
                value_prob = 1
                #automatically join hyphenated words
                for j, word in enumerate(sentence):
                    if word.lemma == '-':
                        tags[j] = ('1', 1)
                for word, (tag, p) in zip(sentence, tags) + [('', ('0', 1))]:
                    if tag == '1':
                        if word.lemma == '-' and not value:
                            continue
                        value.append(word.lemma)
                        value_prob = min(value_prob, p)
                    elif value:
                        if value[-1] == '-':
                            value.pop()
                        if not value:
                            continue
                        v = '_'.join(value).replace('_-_', '-')
                        value = []
                        value_prob = 1
                        #gmina can have the same name as its main city (in fact, it very often does)
                        if v != entity or self.predicate in ['gmina']:
                            values.append((v, value_prob))
            #sort by decreasing probabilities
            values = filter(lambda (_, p): p > confidence_level, values)
            values.sort(key=lambda (_, p): -p)
            values = map(lambda (v, p): (str(int(atof(v))) if is_numeric(v) else v, p), values)
            if verbose:
                print entity, values
            values = [v for v, _ in values]
            if values:
                if self.predicate in numeric_predicates:
                    extracted_values[entity] = values[0]
                    continue
                #to increase precision of extraction (at the cost of recall) in textual relations, 
                #only values that are geographic entities in DBPedia are extracted_valuesurned
                values_identified_as_entities = [
                    v for v in values if lt.is_entity(v)
                ]
                values_identified_as_entities_of_right_type = [
                    v for v in values_identified_as_entities if\
                    any(entities_types.index(t) in lt.entities[v] for t in self.predominant_types)
                ]
                if verbose:
                    print ' '.join(values),
                    print ' '.join(values_identified_as_entities),
                    print ' '.join(values_identified_as_entities_of_right_type)
                if values_identified_as_entities_of_right_type:
                    extracted_values[entity] = values_identified_as_entities_of_right_type[0]
                elif values_identified_as_entities and evaluation_mode:
                    extracted_values[entity] = values_identified_as_entities[0]
                elif self.predicate in ['gmina', 'powiat', quote_plus('województwo')]:
                    extracted_values[entity] = values[0]
        return extracted_values
                   
