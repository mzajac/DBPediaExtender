# -*- coding: utf-8 -*-
import sys
import os
import numpy
from itertools import izip
from collections import defaultdict
from random import shuffle
from pprint import pprint
from string import punctuation
from urllib import quote_plus
from urllib2 import unquote

from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.pipeline import Pipeline

from config import articles_cache_path, models_cache_path, training_limit, verbose, evaluation_mode, numeric_predicates, type_restrictions, save_to_cache
from sparql_access import select_all, select_entities_of_type_in_relation
from pickler import Pickler
from language_tools import LanguageToolsFactory
from article_access import get_article, prepare_articles
from polish_stop_words import stop_words

stop_words = set(stop_words)
lt = LanguageToolsFactory.get_language_tools()
    
def split_camelcase(s):
    ret = []
    word = []
    for letter in s:
        if letter.isupper():
            ret.append(''.join(word))
            word = []
        word.append(letter)
    ret.append(''.join(word))
    return ret
    
def get_sentence_classifier(predicate, sentence_limit=None):
    try:
        ret = Pickler.load(models_cache_path % ('svmmodel-%s.pkl' % predicate))
        ret.classifier.set_params(v__analyzer=lambda x: x)
        return ret
    except IOError:
        return SentenceClassifier(predicate, sentence_limit)
    
class SentenceClassifier:
    def __init__(self, predicate, sentence_limit = None, confidence_level=.75):
        self.predicate = predicate
        self.predicate_words = map(lambda w: w.lower(), split_camelcase(unquote(predicate)))
        self.confidence_level = confidence_level
        self.sentence_limit = sentence_limit
        self.train()
        if save_to_cache:
            #pickle can't save a function, so it's removed before saving
            self.classifier.set_params(v__analyzer=None)
            Pickler.store(self, models_cache_path % ('svmmodel-%s.pkl' % predicate))
            self.classifier.set_params(v__analyzer=lambda x: x)

    def collect_features(self, sentences, threshold=10):
        '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
        if self.sentence_limit < 100:
            threshold = 2
        elif self.sentence_limit < 1000:
            threshold = 5
        vocabulary = defaultdict(int)
        for sentence in sentences:
            for feature in self.get_features(sentence):
                vocabulary[feature] += 1
        return [
            feature for feature, count in vocabulary.iteritems() if count > threshold
        ]
        
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain a reference to the subject of the article, the searched value and if there is more than one such sentence in an article also to at least part of the predicate. Both types of sentences are returned, positive sentences contain also the value.'''
        positive, negative = [], []
        types = ['hrabstwo', 'gmina', 'prowincja', quote_plus('województwo'), 'powiat', 'region']
        for subject, object in names:
            try:
                article = get_article(subject)
            except:
                continue
            pos = []
            object = lt.prepare_value(object, self.predicate)
            best_match = (0, '')
            for sentence in article:
                lemmas = [word.lemma for word in sentence]
                if any(o in lemmas for o in object):
                    if self.predicate not in types or any(p in [l for l in lemmas] for p in self.predicate_words):
                        num_matches = len(set(lemmas) & set(object))
                        if num_matches > best_match[0]:
                            best_match = (num_matches, (sentence, object))
                else:
                    negative.append(sentence)
            if best_match[0]:
                positive.append(best_match[1])
        assert len(positive) > 10, 'Too little training examples.'
        return positive, negative
        
    def train(self):
        if self.predicate in type_restrictions:
            names = select_entities_of_type_in_relation(
                type_restrictions[self.predicate], self.predicate
            )    
        else:
            names = select_all({'p': self.predicate})
        if len(names) > training_limit and self.predicate not in [quote_plus('województwo')]:
            new_names = []
            values_added = set()
            for e, v in names:
                if v not in values_added:
                    values_added.add(v)
                    new_names.append((e, v))
            names = new_names
        names = names[: training_limit]
        if verbose:
            print '%d articles processed during training.' % len(names)
        if evaluation_mode:
            #make sure that entities that will be used in evaluation, are not used in training
            from evaluator import get_test_data
            names = filter(lambda (entity, _): entity not in get_test_data(self.predicate)[0], names)
        #prepare articles about subjects
        prepare_articles(zip(*names)[0])
        positive, negative = self.collect_sentences(names)
        positive = positive[: self.sentence_limit]
        if verbose:
            print 'Sentences selected for training (%d total):' % len(positive)
            for s, v in positive:
                print ' '.join(v), ' ', ' '.join([w.lemma for w in s])
            print
        self.extractor_training_data = positive[:]
        positive = map(lambda (s, v): s, positive)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        vocabulary = self.collect_features(positive)
        if verbose:
            print 'Words considered as features:'
            print vocabulary
            print
        self.classifier = Pipeline([
            ('v', CountVectorizer(analyzer=lambda x: x, vocabulary=vocabulary, binary=True)),
            ('c', SVC(kernel='linear', probability=True)),
        ]) 
        self.classifier.fit(map(self.get_features, sentences), classes)
        self.get_most_informative_features()
        
    def get_most_informative_features(self, n=10):
        #works only with a linear kernel
        try:
            vectorizer = self.classifier.named_steps['v']
            clf = self.classifier.named_steps['c']
            feature_relevance = list(reversed(sorted(zip(clf.coef_[0].toarray()[0], vectorizer.get_feature_names()))))[:n]
            #filter out nondiscriminating features
            feature_relevance = filter(lambda (v, _): v >= .5, feature_relevance)
            if verbose:
                print 'Most informative features:'
                for value, name in feature_relevance:
                    print '%s %.2f' % (name, value)
                print
        except ValueError:
            pass
        
    def extract_sentences(self, entities):
        articles = prepare_articles(entities)
        extracted_sentences = defaultdict(list)
        if verbose:
            print 'Classifying sentences:'
        for entity in entities:
            try:
                article = get_article(entity)
            except:
                continue
            if not article:
                continue
            if verbose:
                print entity
            probabilities = [prob[1] for prob in self.classifier.predict_proba(map(self.get_features, article))]
            #for each article return all sentences with scores > confidence_level
            for sentence, p in izip(article, probabilities):
                if p > self.confidence_level:
                    extracted_sentences[entity].append(sentence)
                    if verbose:
                        print '***', '%.2f' % p, ' '.join([w.segment for w in sentence])
                elif verbose:
                    print '%.2f' % p, ' '.join([w.segment for w in sentence])
            if verbose:
                print
        return extracted_sentences
        
    def get_features(self, sentence):
        return filter(
            lambda w: w.decode('utf-8')[0].islower() and w not in stop_words, 
            [word.lemma for word in sentence]
        )
       
