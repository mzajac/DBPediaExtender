#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from sentence_classifier import SentenceClassifier, evaluate_sentence_classifier

def main():
    predicates = ['populationTotal', 'capital', 'source']
    for p in predicates[1:2]:
        evaluate_sentence_classifier(p)
            
if __name__ == '__main__':
    main()

