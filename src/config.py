#encoding: utf-8
#language code
lang = 'pl'
data_source = "http://dbpedia.org" if lang == 'en' else 'http://%s.dbpedia.org' % lang

verbose = True
evaluation_mode = 1
#limits number of candidates for learning
candidates_limit = 1000
#limits number of triples used in training
training_limit = 100#00

#Polish
predicates = [
    'populacja',
    'stolica',
    'uchodziDo',
    'źródłoGdzie',
    'uchodziGdzie',
][1:2]


numeric_predicates = set([predicates[0]])

sparql_endpoint = "http://localhost:8890/sparql/"

main_path = '/home/mz/Dokumenty/dbpedia-enricher/'
data_path = '/media/Data/Virtuoso/'

#Relative paths
ext_path = main_path + 'ext/'
raw_articles_path = data_path + '%s/articles' % lang
wikidump_path = data_path + '%s/wiki' % lang
triples_path = data_path + '%s/triples' % lang
cache_path = main_path + 'cache/'
entities_path = cache_path + '%s/entities.pkl' % lang
synonyms_path = cache_path + '%s/synonyms.pkl' % lang
articles_cache_path = cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = main_path + 'results/%s/' % lang
tests_path = main_path + 'tests/%s/' % lang

#Software paths
java_path = '/usr/lib/jvm/java-6-sun-1.6.0.26/bin/java'
mallet_path = ext_path + 'mallet-0.4/bin/'

