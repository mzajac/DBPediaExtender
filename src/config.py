#language code
lang = 'en'
#character used to signify if a preceding segment is part of an anchor
#node: should be an ASCII symbol not present in Wikitext
anchor_sign = '~' 

verbose = True
evaluation_mode = False
candidates_limit = 100
training_limit = 10

predicates = [
    'populationTotal',
    'capital',
    'source',
    'discharge',
    'areaTotal',
    'mountainRange',
    'elevation',
][1:2]

data_source = "http://dbpedia.org"
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
