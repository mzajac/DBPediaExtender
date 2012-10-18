#!/usr/bin/env python
import sys
from itertools import izip
from collections import defaultdict

from config import tests_path
from sparql_access import select_all, select_entities_of_type_in_relation
from sentence_classifier import SentenceClassifier

predicate = 'populacja'
test_data_limit = 1

entities_f = open(tests_path + '%s/entities' % predicate, 'w')

names = select_all({'p': predicate})[: test_data_limit]
#names = select_entities_of_type_in_relation(type, predicate)[: test_data_limit]
subjects, objects = zip(*list(names))
values = defaultdict(list)
for subject, value in names:
    values[subject].append(value)
articles, _ = SentenceClassifier.get_articles(subjects)
print articles
articles = dict(zip(subjects, articles))
for subject, value in values.iteritems():
    article = articles[subject]
    print subject, value[0]
    for sentence in article:
        print ' '.join(sentence)
    print
    print >>entities_f, subject
