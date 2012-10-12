# -*- coding: utf-8 -*-
import sys
import os
import numpy
from itertools import izip
from collections import defaultdict
from random import shuffle

from sklearn.svm import SVC
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

from config import articles_cache_path, models_cache_path, training_limit, verbose, evaluation_mode
from sparql_access import select_all
from pickler import Pickler
from language_tools import LanguageToolsFactory, is_numeric
from article_access import get_article, prepare_articles

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
        
    def collect_sentences(self, names):
        '''classifies all sentences based on the fact that they contain a reference to the subject of the article, the searched value and if there is more than one such sentence in an article also to at least part of the predicate'''
        positive, negative = [], []
        for subject, object in names:
            if is_numeric(object):
                object = str(int(round(float(object))))
            if object == 0:
                continue
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
        self.extractor_training_data = positive[:]
        positive = map(lambda (s, v): s, positive)
        #decreases number of negative examples to the number of positive examples to avoid unbalanced data
        shuffle(negative)
        negative = negative[: len(positive)]
        sentences = positive + negative
        classes = [True] * len(positive) + [False] * len(negative)
        #vocabulary is collected only from positive sentences
        self.classifier = Pipeline([
            ('v', CountVectorizer(analyzer=lambda x: x)),
            ('t', TfidfTransformer()),
            ('c', SVC(kernel='linear')),
        ])
        lemmas_list = [[word.lemma for word in sentence] for sentence in sentences]
        self.classifier.fit(lemmas_list, classes)
        self.entities = set(
            e for e, v in names
        )
        
    def predict(self, vectors):
        return map(int, list(self.classifier.predict(vectors)))
        
    def extract_sentences(self, entities):
        articles = prepare_articles(entities)
        ret_entities, ret_sentences = [], [] 
        for entity in entities:
            try:
                article = get_article(entity)
            except:
                continue
            lemmas_list = [[word.lemma for word in sentence] for sentence in article]
            segments_list = [[word.segment for word in sentence] for sentence in article]
            classes = self.predict(lemmas_list)
            if verbose:
                print entity
                if classes.count(1) >= 1:
                    print ' *** ' + ' '.join(segments_list[classes.index(1)])
                print '\n'.join(map(lambda s: ' '.join(s), article))
                print
            if classes.count(1) >= 1:
                ret_entities.append(entity)
                ret_sentences.append(article[classes.index(1)])
        return ret_entities, ret_sentences
       
