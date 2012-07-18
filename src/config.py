#language code
lang = 'en'
data_source = "http://dbpedia.org" if lang == 'en' else 'http://%s.dbpedia.org' % lang

verbose = False
evaluation_mode = True
#limits number of candidates for learning
candidates_limit = 100
#limits number of triples used in training
training_limit = 10000

predicates = [
    'populationTotal',
    'capital',
    'source',
    'discharge',
    'areaTotal',
    'mountainRange',
    'elevation',
][0:1]

sparql_endpoint = "http://localhost:8890/sparql/"

main_path = '/home/mz/Dokumenty/dbpedia-enricher/'
ext_path = main_path + 'ext/'
stanford_path = ext_path + 'stanford-parser'
java_path = '/usr/lib/jvm/java-6-sun-1.6.0.26'
mallet_path = ext_path + 'mallet-0.4'
raw_articles_path = '/media/Data/Virtuoso/articles'
cache_path = main_path + 'cache/'
articles_cache_path = cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = main_path + 'results/%s/' % lang
tests_path = main_path + 'tests/%s/' % lang
