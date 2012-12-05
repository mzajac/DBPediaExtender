#encoding: utf-8

from urllib import quote_plus
import os

verbose = True
#evaluation mode: 0 -> no evaluation, 1 -> performs evaluation using data from the tests/ directory
evaluation_mode = 0
#limits number of candidates for learning
candidates_limit = 10000
#limits number of triples used in training
training_limit = 10000
#use spejd (this increases running time)
use_parser = True

#predicates to learn
predicates = [
    'populacja',
    'stolica',
    'uchodziDo',
    'gmina',
    'powiat',
    'województwo',
    'region',
    'departament',
    'prowincja',
    'długość'
#    'źródłoGdzie',
#    'uchodziGdzie',
][9:10]
predicates = map(quote_plus, predicates)
numeric_predicates = set(['populacja', quote_plus('długość')])

#Some predicates are too broad and it's necessary to specify we are only interested in entities of specific type.
type_restrictions = {
    quote_plus('długość'): 'Stream',
}

sparql_endpoint = "http://localhost:8890/sparql/"
lang = 'pl'
data_source = "http://dbpedia.org" if lang == 'en' else 'http://%s.dbpedia.org' % lang
main_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) + '/'

#Relative paths
data_path = main_path + 'data/'
ext_path = main_path + 'ext/'
raw_articles_path = data_path + '%s/articles' % lang
wikidump_path = data_path + '%s/wiki' % lang
cache_path = main_path + 'cache/'
entities_path = cache_path + '%s/entities.pkl' % lang
synonyms_path = cache_path + '%s/synonyms.pkl' % lang
articles_cache_path = cache_path + '%s/articles_spejd/%%s' % lang if use_parser else cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = main_path + 'results/%s/' % lang
tests_path = main_path + 'tests/%s/' % lang
spejd_path = ext_path + 'spejd-1.3.6'

