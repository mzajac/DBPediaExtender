# -*- coding: utf-8 -*-
import sys
import os
import numpy
from itertools import izip
from collections import defaultdict
from random import shuffle
from pprint import pprint
from string import punctuation

from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.pipeline import Pipeline

from config import articles_cache_path, models_cache_path, training_limit, verbose, evaluation_mode, numeric_predicates
from sparql_access import select_all
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
    
def get_sentence_classifier(predicate, confidence_level=None):
    if confidence_level:
        return SentenceClassifier(predicate, confidence_level)
    return SentenceClassifier(predicate)
    
class SentenceClassifier:
    def __init__(self, predicate=None, confidence_level=.8):
        if predicate is not None:
            self.predicate = predicate
            self.predicate_words = map(lambda w: w.lower(), split_camelcase(predicate))
            self.confidence_level = confidence_level
            self.train()

    def collect_features(self, sentences, threshold=5):
        '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
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
        for subject, object in names:
            try:
                article = get_article(subject)
            except:
                continue
            pos = []
            object = lt.prepare_value(object, self.predicate)
            object_filtered = filter(lambda w: w and not w[0].islower(), object)
            for sentence in article:
                lemmas = [word.lemma for word in sentence]
                if any(o in lemmas for o in object_filtered):
                    pos.append((sentence, object))
                else:
                    negative.append(sentence)
            if self.predicate == 'stolica':
                pos = filter(lambda (s, _): any(word in [w.lemma for w in s] for word in self.predicate_words), pos)
            positive += pos
        return positive, negative
        
    def train(self):
        names = select_all({'p': self.predicate})
#        shuffle(names)
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
        self.most_informative_features = self.get_most_informative_features()
        self.entities = set(
            e for e, v in names
        )
        
    def get_most_informative_features(self, n=10):
        #works only with a linear kernel
        try:
            vectorizer = self.classifier.named_steps['v']
            clf = self.classifier.named_steps['c']
            feature_relevance = list(reversed(sorted(zip(clf.coef_[0].toarray()[0], vectorizer.get_feature_names()))))[:n]
            #filter out nondiscriminating features
            feature_relevance = filter(lambda (v, _): v >= 1.3, feature_relevance)
            if verbose:
                print 'Most informative features:'
                for value, name in feature_relevance:
                    print '%s %.2f' % (name, value)
                print
            return zip(*feature_relevance)[1]
        except ValueError:
            return []
        
    def extract_sentences(self, entities):
        articles = prepare_articles(entities)
#        ret_entities, ret_sentences = [], []
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
#                elif verbose:
#                    print '%.2f' % p, ' '.join([w.segment for w in sentence])
            if verbose:
                print
        return extracted_sentences
        
    def get_features(self, sentence):
        lemmas = [word.lemma for word in sentence]
        hypernyms = []
        for word in sentence:
            hypernyms += lt.get_hypernyms(word)
        lemmas += hypernyms
        return filter(lambda w: w.decode('utf-8').isalpha() and w not in stop_words, lemmas)
       
