#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from sentence_classifier import evaluate_sentence_classifier, learn_new_triples

def main():
    predicates = ['populationTotal', 'capital', 'source']
    for p in predicates[0:1]:
        learn_new_triples(p)
            
if __name__ == '__main__':
    main()

