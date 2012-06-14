#!/usr/bin/env python
import sys
import os
import numpy
from pprint import pprint
from itertools import izip
from collections import defaultdict
from random import shuffle

from sklearn.svm import SVC
from sklearn.feature_extraction.text import CountVectorizer

from sparql_access import select_all
from article_access import get_article, ArticleNotFoundError
from pickler import Pickler
from language_tools import LanguageToolsFactory

lang = 'en'
lt = LanguageToolsFactory.get_language_tools(lang)

def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i : i+n]) for i in xrange(len(lst) - n + 1))
    
def extract_training_features(sentence):
    sentence = map(lambda w: w.decode('utf8').lower(), sentence)
    sentence = lt.remove_nonwords(sentence)
    sentence = lt.remove_stop_words(sentence)
    sentence = lt.lemmatize(sentence)
    return sentence
    
def collect_training_sentences(names, articles):
    '''classifies all sentences based on the fact that they contain reference to other_name'''
    positive, negative = [], [] 
    for (subject, object), (s_article, o_article) in izip(names, articles):
        for article, other_name in [(s_article, object), (o_article, subject)]:
            if article:
                for sentence in article:
                    sentence = sentence.replace(subject, '')
                    sentence = sentence.replace(object, '')
                    sentence = sentence.split()
                    #TODO: remove subject and object names
                    sentence = lt.convert_to_base_form(sentence)
                    if contains_sublist(sentence, other_name.split()):
                        positive.append(extract_training_features(sentence))
                    else:
                        negative.append(extract_training_features(sentence))
    return positive, negative
    
def collect_words(sentences, threshold=1):
    '''creates a vocabulary of words occurring in the sentences that occur more than threshold times'''
    vocabulary = defaultdict(int)
    for sentence in sentences:
        for word in sentence:
            vocabulary[word] += 1
    return [
        word for word, count in vocabulary.iteritems() if count > threshold
    ]
       
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
    
def learn_predicate_classifier(p):
    names = select_all({'p': p})
    names = names[: 10]
    articles = get_articles(names)
    positive, negative = collect_training_sentences(names, articles)
    #decreases number of negative examples to the number of positive examples to avoid unbalanced data
    shuffle(negative)
    negative = negative[: len(positive)]
    print '+', positive
    print '-', negative
    sentences = positive + negative
    classes = [True * len(positive)] + [False * len(negative)]
    vocabulary = collect_words(sentences)
    cv = CountVectorizer(binary=True, dtype=numpy.bool, analyzer=lambda x: x, vocabulary=vocabulary)
    vectors = cv.fit_transform(sentences)
    classifier = SVC(class_weight='auto')
    classifier.fit(vectors, classes)
    return classifier
    
def experiment():
    predicates = ['populationTotal', 'capital']
    for p in predicates[:1]:
        classifier = learn_predicate_classifier(p)
#        classifier.predict()

def main():
    experiment()
            
if __name__ == '__main__':
    main()

