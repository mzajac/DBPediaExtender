#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import numpy
from pprint import pprint
from itertools import izip
from collections import defaultdict
from random import shuffle

from sklearn.svm import SVC
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import metrics

from sparql_access import select_all
from article_access import get_article, ArticleNotFoundError
from pickler import Pickler
from language_tools import LanguageToolsFactory

lang = 'en'
lt = LanguageToolsFactory.get_language_tools(lang)

def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i : i+n]) for i in xrange(len(lst) - n + 1))
    
class SentenceClassifier:
    def __init__(self, predicate):
        self.filename = 'model-%s.pkl' % predicate
        self.predicate = predicate
        
    @staticmethod
    def collect_words(sentences, threshold=1):
        '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
        vocabulary = defaultdict(int)
        for sentence in sentences:
            for word in sentence:
                vocabulary[word] += 1
        return [
            word for word, count in vocabulary.iteritems() if count > threshold
        ]
        
    @staticmethod 
    def get_articles(names):
        articles = []
        for i, (subject, object) in enumerate(names):
            try:
                s = get_article(subject)
            except ArticleNotFoundError:
                s = None
            try:
                o = get_article(object)
            except ArticleNotFoundError:
                o = None
            articles.append((s, o))
            names[i] = subject.replace('_', ' '), object.replace('_', ' ')
        articles = map(lambda (s, o): (lt.tokenize(s), lt.tokenize(o)), articles)
        return articles
      
    @staticmethod  
    def collect_sentences(names):
        '''classifies all sentences based on the fact that they contain reference to searched value'''
        articles = SentenceClassifier.get_articles(names)
        positive, negative = [], [] 
        for (subject, object), (s_article, o_article) in izip(names, articles):
            for article, other_name in [(s_article, object), (o_article, subject)]:
                if article:
                    for sentence in article:
                        sentence = lt.prepare_sentence(sentence)
                        #TODO: removes all references to other articles
                        if contains_sublist(sentence, other_name.split()):
                            positive.append(lt.extract_vector_of_words(sentence))
                        else:
                            negative.append(lt.extract_vector_of_words(sentence))
        return positive, negative
        
    @staticmethod
    def convert_to_vector_space(names, vocabulary=None):
        positive, negative = SentenceClassifier.collect_sentences(names)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        #vocabulary is collected only from positive sentences
        if vocabulary is None:
            vocabulary = SentenceClassifier.collect_words(positive)
        cv = CountVectorizer(binary=True, dtype=numpy.bool, analyzer=lambda x: x, vocabulary=vocabulary)
        vectors = cv.transform(sentences)
        return vectors, classes, vocabulary
        
    def train(self, names=None):
        try:
            self.classifier = Pickler.load(self.filename)
            return
        except IOError:
            pass
        if names is None:
            names = select_all({'p': self.predicate})
            names = names
        vectors, classes, self.vocabulary = self.convert_to_vector_space(names)
        self.classifier = SVC(class_weight='auto')
        self.classifier.fit(vectors, classes)
        Pickler.store(self, self.filename)
        
    def predict(self, sentences):
        sentences = map(lambda s: lt.prepare_sentence(s), sentences)
        sentences = map(lambda s: lt.extract_vector_of_words(s), sentences)
        cv = CountVectorizer(binary=True, dtype=numpy.byte, analyzer=lambda x: x, vocabulary=self.vocabulary)
        vectors = cv.transform(sentences)
        return classifier.predict(vectors)
        
def evaluate_sentence_classifier(p):
    """divides entities into test and training sets (10% and 90% of data) and evaluates the classifier"""
    names = select_all({'p': p})[:5]
    shuffle(names)
    test_set = names[: len(names) / 10]
    training_set = names[len(names) / 10 :]
    sc = SentenceClassifier(p)
    sc.train(training_set)
    #TODO


