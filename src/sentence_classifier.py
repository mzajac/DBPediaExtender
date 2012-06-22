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
from sklearn.metrics import classification_report

from sparql_access import select_all
from article_access import get_article, ArticleNotFoundError
from pickler import Pickler
from language_tools import LanguageToolsFactory

lang = 'en'
lt = LanguageToolsFactory.get_language_tools(lang)

def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i : i+n]) for i in xrange(len(lst) - n + 1))
    
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
    
class SentenceClassifier:
    def __init__(self, predicate):
        self.filename = 'model-%s.pkl' % predicate
        self.predicate = predicate
        self.predicate_words = lt.lemmatize(split_camelcase(predicate))
        self.predicate_words = map(lambda w: w.lower(), self.predicate_words)
#        try:
#            self.classifier = Pickler.load(self.filename)
#            return
#        except IOError:
#            pass
        
    @staticmethod
    def collect_words(sentences, threshold=5):
        '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
        vocabulary = defaultdict(int)
        for sentence in sentences:
            for word in sentence:
                vocabulary[word] += 1
        return dict(
            [(word, count) for word, count in vocabulary.iteritems() if count > threshold]
        )
        
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
      
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain reference to searched value and to at least part of the predicate'''
        articles = SentenceClassifier.get_articles(names)
        positive, negative = [], [] 
        for (subject, object), (s_article, o_article) in izip(names, articles):
            for article, other_name in [(s_article, object), (o_article, subject)]:
                if article:
                    for sentence in article:
                        sentence = lt.prepare_sentence(sentence)
                        if contains_sublist(sentence, other_name.split()):
                            sentence = lt.extract_vector_of_words(sentence)
                            if any(word in sentence for word in self.predicate_words):
                                positive.append(sentence)
                        else:
                            negative.append(sentence)
        return positive, negative
        
    def convert_to_vector_space(self, names, vocabulary=None):
        positive, negative = self.collect_sentences(names)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        negative = map(lambda s: lt.extract_vector_of_words(s), negative)
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        #vocabulary is collected only from positive sentences
        if vocabulary is None:
            vocabulary = SentenceClassifier.collect_words(positive)
        cv = CountVectorizer(binary=True, dtype=numpy.bool, analyzer=lambda x: x, vocabulary=vocabulary)
        vectors = cv.transform(sentences) if sentences else []
        return vectors, classes, vocabulary, sentences
        
    def train(self, names=None):
        if names is None:
            names = select_all({'p': self.predicate})
            names = names
        vectors, classes, self.vocabulary, _ = self.convert_to_vector_space(names)
        self.classifier = SVC()
        self.classifier.fit(vectors, classes)
        Pickler.store(self, self.filename)
        
    def predict(self, vectors):
        return self.classifier.predict(vectors)
        
def evaluate_sentence_classifier(p):
    """divides entities into test and training sets (10% and 90% of data) and evaluates the classifier"""
    names = select_all({'p': p})[:100]
    shuffle(names)
    test_set = names[: len(names) / 10]
    training_set = names[len(names) / 10 :]
    sc = SentenceClassifier(p)
    sc.train(training_set)
    vectors, true_classes, _, sentences = sc.convert_to_vector_space(test_set, sc.vocabulary)
    if not vectors:
        return
    predicted_classes = sc.predict(vectors)
    print classification_report(true_classes, predicted_classes)
    
