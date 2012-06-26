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
    
def get_sentence_classifier(predicate):
    try:
        return Pickler.load('model-%s.pkl' % predicate)
    except IOError:
        return SentenceClassifier(predicate)
    
class SentenceClassifier:
    def __init__(self, predicate):
        self.predicate = predicate
        self.predicate_words = lt.lemmatize(split_camelcase(predicate))
        self.predicate_words = map(lambda w: w.lower(), self.predicate_words)
        self.vocabulary = None
        self.train()
        Pickler.store(self, 'model-%s.pkl' % predicate)
        
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
        for i, name in enumerate(names):
            try:
                articles.append(lt.tokenize(get_article(name)))
            except ArticleNotFoundError:
                articles.append(None)
        return articles
      
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain reference to searched value and to at least part of the predicate'''
        subjects, objects = zip(*list(names)) #unzip
        subject_articles = SentenceClassifier.get_articles(subjects)
        object_articles = SentenceClassifier.get_articles(objects)
        positive, negative = [], []
        for subject, object, subject_article, object_article in izip(subjects, objects, subject_articles, object_articles):
            for article, other_name in [(subject_article, object), (object_article, subject)]:
                if article:
                    for sentence in article:
                        sentence = lt.prepare_sentence(sentence)
                        if contains_sublist(sentence, other_name.replace('_', ' ').split()):
                            sentence = lt.extract_vector_of_words(sentence)
                            if any(word in sentence for word in self.predicate_words):
                                positive.append(sentence)
                        else:
                            negative.append(sentence)
        return positive, negative
        
    def convert_to_vector_space(self, sentences):
        cv = CountVectorizer(binary=True, dtype=numpy.bool, analyzer=lambda x: x, vocabulary=self.vocabulary)
        vectors = cv.transform(sentences) if sentences else []
        return vectors, sentences
        
    def train(self, names=None):
        if names is None:
            names = select_all({'p': self.predicate})[:100]
        positive, negative = self.collect_sentences(names)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        negative = map(lambda s: lt.extract_vector_of_words(s), negative)
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        #vocabulary is collected only from positive sentences
        self.vocabulary = SentenceClassifier.collect_words(positive)
        vectors, _ = self.convert_to_vector_space(sentences)
        self.classifier = SVC()
        self.classifier.fit(vectors, classes)
        
    def predict(self, vectors):
        return map(int, list(self.classifier.predict(vectors)))
        
    def extract_sentences(self, entities):
        articles = SentenceClassifier.get_articles(entities)
        ret_entities, ret_sentences = [], [] 
        for entity, article in izip(entities, articles):
            article = map(lambda s: lt.prepare_sentence(s), article)
            article = map(lambda s: lt.extract_vector_of_words(s), article)
            vectors, _ = self.convert_to_vector_space(article)
            classes = self.predict(vectors)
            if classes.count(1) == 1:
                ret_entities.append(entity)
                ret_sentences.append(article[classes.index(1)])
        return ret_entities, ret_sentences
        
        
def evaluate_sentence_classifier(predicate):
    """divides entities into test and training sets (10% and 90% of data) and evaluates the classifier"""
    names = select_all({'p': predicate})[:100]
    shuffle(names)
    test_set = names[: len(names) / 10]
    training_set = names[len(names) / 10 :]
    sc = get_sentence_classifier(predicate)
    sc.train(training_set)
#    vectors, true_classes, _, sentences = sc.convert_to_vector_space(test_set)
#    if not vectors:
#        return
#    predicted_classes = sc.predict(vectors)
#    print classification_report(true_classes, predicted_classes)
       
