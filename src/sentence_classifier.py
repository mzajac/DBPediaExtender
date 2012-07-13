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

from config import lang, articles_cache_path, models_cache_path
from sparql_access import select_all
from article_access import get_article, ArticleNotFoundError
from pickler import Pickler
from language_tools import LanguageToolsFactory

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
#        print articles_cache_path % ('model-%s.pkl' % predicate)
        return Pickler.load(models_cache_path % ('model-%s.pkl' % predicate))
    except IOError:
        return SentenceClassifier(predicate)
    
class SentenceClassifier:
    def __init__(self, predicate):
        self.predicate = predicate
        self.predicate_words = lt.lemmatize(split_camelcase(predicate))
        self.predicate_words = map(lambda w: w.lower(), self.predicate_words)
        self.vocabulary = None
        self.train()
        Pickler.store(self, models_cache_path % ('model-%s.pkl' % predicate))
        
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
            name = name.replace('/', '_')
            try:
                articles.append(Pickler.load(articles_cache_path % name))
            except IOError:
                try:
                    article = lt.tokenize(get_article(name))
                    articles.append(article)
                    Pickler.store(article, articles_cache_path % name)
                except ArticleNotFoundError:
                    articles.append(None)
        return articles
      
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain a reference to the searched value and if there is more than one such sentence in an article also to at least part of the predicate'''      
        subjects, objects = zip(*list(names)) #unzip
        subject_articles = SentenceClassifier.get_articles(subjects)
        object_articles = SentenceClassifier.get_articles(objects)
        positive, negative = [], []
        for subject, object, subject_article, object_article in izip(subjects, objects, subject_articles, object_articles):
            for article, other_name in [(subject_article, object), (object_article, subject)]:
                if article and other_name != '0': #there is no point in looking for occurences of zero
                    pos = []
                    for sentence in article:
                        sentence = lt.prepare_sentence(sentence)
                        original_sentence = sentence[:]
                        name_as_sublist = other_name.replace('_', ' ').split()
                        if contains_sublist(sentence, name_as_sublist):
                            sentence = lt.extract_vector_of_words(sentence)
                            pos.append((sentence, original_sentence, name_as_sublist))
                        else:
                            negative.append(sentence)
                    #if there is exactly one sentence referring to the searched value, simply add it to positive examples
                    #if more select only sentences containing at least part of the predicate
                    if len(pos) > 1:
                        pos = filter(lambda (s, os, v): any(word in s for word in self.predicate_words), pos)
                    positive += pos
        return positive, negative
        
    def convert_to_vector_space(self, sentences):
        cv = CountVectorizer(analyzer=lambda x: x, vocabulary=self.vocabulary)
        vectors = cv.transform(sentences) if sentences else []
        return vectors, sentences
        
    def train(self, names=None):
        if names is None:
            names = select_all({'p': self.predicate})[:1000]
        print len(names)
        positive, negative = self.collect_sentences(names)
        self.extractor_training_data = map(lambda (s, os, v): (os, v), positive)
        positive = map(lambda (s, os, v): s, positive)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        negative = map(lambda s: lt.extract_vector_of_words(s), negative)
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        #vocabulary is collected only from positive sentences
        self.vocabulary = SentenceClassifier.collect_words(positive)
        vectors, _ = self.convert_to_vector_space(sentences)
        self.classifier = SVC(kernel='linear')
        self.classifier.fit(vectors, classes)
        
    def predict(self, vectors):
        return map(int, list(self.classifier.predict(vectors)))
        
    def extract_sentences(self, entities, verbose=False):
        articles = SentenceClassifier.get_articles(entities)
        ret_entities, ret_sentences = [], [] 
        for entity, article in izip(entities, articles):
            article = map(lambda s: lt.prepare_sentence(s), article)
            sentences = map(lambda s: lt.extract_vector_of_words(s), article)
            vectors, _ = self.convert_to_vector_space(sentences)
            classes = self.predict(vectors)
            if verbose:
                print entity
                if classes.count(1) >= 1:
                    print ' *** ' + ' '.join(article[classes.index(1)])
                print '\n'.join(map(lambda s: ' '.join(s), article))
                print
            if classes.count(1) >= 1:
                ret_entities.append(entity)
                ret_sentences.append(article[classes.index(1)])
        return ret_entities, ret_sentences
       
