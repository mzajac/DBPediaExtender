lang = 'en'
anchor_sign = '~'

data_source = "http://dbpedia.org"
sparql_endpoint = "http://localhost:8890/sparql/"

predicates = [
    'populationTotal',
    'capital',
    'source',
    'discharge',
    'areaTotal',
    'mountainRange',
    'elevation',
][0:1]

opennlp_path = '/home/mz/Dokumenty/dbpedia-enricher/ext/opennlp-tools-1.5.0'
stanford_path = '/home/mz/Dokumenty/dbpedia-enricher/ext/stanford-parser'
java_path = '/usr/lib/jvm/java-6-sun-1.6.0.26'
mallet_path = '/home/mz/Dokumenty/dbpedia-enricher/ext/mallet-0.4'

raw_articles_path = '/media/Data/Virtuoso/articles'
cache_path = '/home/mz/Dokumenty/dbpedia-enricher/cache/'
articles_cache_path = cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = '/home/mz/Dokumenty/dbpedia-enricher/results/%s/' % lang
tests_path = '/home/mz/Dokumenty/dbpedia-enricher/tests/%s/' % lang
