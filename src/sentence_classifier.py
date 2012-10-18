# -*- coding: utf-8 -*-
import sys
import os
import numpy
from itertools import izip
from collections import defaultdict
from random import shuffle
from pprint import pprint

from sklearn.svm import SVC
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

from config import articles_cache_path, models_cache_path, training_limit, verbose, evaluation_mode
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
    
def get_sentence_classifier(predicate):
    try:
        return Pickler.load(models_cache_path % ('model-%s.pkl' % predicate))
    except IOError:
        return SentenceClassifier(predicate)
    
class SentenceClassifier:
    def __init__(self, predicate=None):
        if predicate is not None:
            self.predicate = predicate
            self.predicate_words = map(lambda w: w.lower(), split_camelcase(predicate))
            self.train()
#            Pickler.store(self, models_cache_path % ('model-%s.pkl' % predicate))

    @staticmethod
    def collect_words(sentences, threshold=5):
        '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
        vocabulary = defaultdict(int)
        for sentence in sentences:
            for word in sentence:
                vocabulary[word] += 1
        return [word for word, count in vocabulary.iteritems() if count > threshold]
        
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain a reference to the subject of the article, the searched value and if there is more than one such sentence in an article also to at least part of the predicate. Both types of sentences are returned, positive sentences contain also the value.'''
        positive, negative = [], []
        for subject, object in names:
            object = lt.prepare_value(object, self.predicate)
            try:
                article = get_article(subject)
            except:
                continue
            pos = []
            for sentence in article:
                lemmas = [word.lemma for word in sentence]
                if object in lemmas:
                    pos.append((sentence, object))
                else:
                    negative.append(sentence)
            #if there is exactly one sentence referring to the searched value, simply add it to positive examples
            #if more select only sentences containing at least part of the predicate
            if len(pos) > 1:
                pos = filter(lambda (s, _): any(word in [w.lemma for w in s] for word in self.predicate_words), pos)
            positive += pos
        return positive, negative
        
    def train(self):
        names = select_all({'p': self.predicate})[: training_limit]
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
                print v, ' '.join([w.lemma for w in s])
            print
        self.extractor_training_data = positive[:]
        positive = map(lambda (s, v): s, positive)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        vocabulary = SentenceClassifier.collect_words(map(self.get_lemmas, positive))
        if verbose:
            print 'Words considered as features:'
            print vocabulary
            print
        self.classifier = Pipeline([
            ('v', TfidfVectorizer(analyzer=lambda x: x, vocabulary=vocabulary)),
            ('c', SVC(kernel='rbf')),
        ])
        self.classifier.fit(map(self.get_lemmas, sentences), classes)
        self.entities = set(
            e for e, v in names
        )     
        
    def extract_sentences(self, entities):
        articles = prepare_articles(entities)
        ret_entities, ret_sentences = [], []
        if verbose:
            print 'Classifying sentences:'
        for entity in entities:
            try:
                article = get_article(entity)
            except:
                continue
            if verbose:
                print entity
            classes = self.classifier.predict(map(self.get_lemmas, article))
            for sentence, cls in izip(article, classes):
                if verbose:
                    if cls:
                        print ' *** ',
                        print ' '.join([w.segment for w in sentence]), ' | ', ' '.join([w.lemma for w in sentence])
                if cls:
                    ret_entities.append(entity)
                    ret_sentences.append(sentence)
            if verbose:
                print
        sys.exit()
        return ret_entities, ret_sentences
        
    def get_lemmas(self, sentence):
        lemmas = [word.lemma for word in sentence]
        return filter(lambda w: len(w) > 2 and w[0].islower() and not w.isdigit() and w not in stop_words, lemmas)
       
