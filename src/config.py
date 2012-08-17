#language code
lang = 'en'#'pl'
data_source = "http://dbpedia.org" if lang == 'en' else 'http://%s.dbpedia.org' % lang

verbose = True
evaluation_mode = True
#limits number of candidates for learning
candidates_limit = 100
#limits number of triples used in training and evaluation
training_limit = 10000

predicates = [
    'populationTotal',
    'capital',
    'source',
    'discharge',
    'areaTotal',
    'mountainRange',
    'elevation',
    'riverMouth',
][6:7]

sparql_endpoint = "http://localhost:8890/sparql/"

main_path = '/home/mz/Dokumenty/dbpedia-enricher/'
ext_path = main_path + 'ext/'
stanford_path = ext_path + 'stanford-parser'
stanford_ner_path = ext_path + 'stanford-ner-2012-07-09/'
ner_model_path = stanford_ner_path + 'classifiers/english.conll.4class.distsim.crf.ser'
ner_jar_path = stanford_ner_path + 'stanford-ner.jar'
java_path = '/usr/lib/jvm/java-6-sun-1.6.0.26/bin/java'
mallet_path = ext_path + 'mallet-0.4/bin/'
raw_articles_path = '/media/Data/Virtuoso/articles'
wikidump_path = '/media/Data/Virtuoso/wiki'
cache_path = main_path + 'cache/'
entities_path = cache_path + '%s/entities.pkl' % lang
synonyms_path = cache_path + '%s/synonyms.pkl' % lang
articles_cache_path = cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = main_path + 'results/%s/' % lang
tests_path = main_path + 'tests/%s/' % lang
