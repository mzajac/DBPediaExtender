#encoding: utf-8

from urllib import quote_plus
import os

verbose = True
#evaluation mode: 0 -> no evaluation, 1 -> performs evaluation using data from the tests/ directory
evaluation_mode = 1
#limits number of candidates for learning
candidates_limit = 1000000
#limits number of triples used in training
training_limit = 10000
#use Wordnet synsets as features
use_wordnet = False
#use a parser (this increases running time)
use_parser = False
parser_type = 'dependency' #'shallow'

#predicates to learn
predicates = [
    'populacja',
    'stolica',
    'uchodziDo',
    'gmina',
    'powiat',
    'województwo',
    'region',
    'prowincja',
    'długość',
    'hrabstwo',
    'powDorzecza',
    'średniPrzepływ',
    'gęstość',
    'powierzchnia',
    'stan',
][14:15]
predicates = map(quote_plus, predicates)
numeric_predicates = set(map(quote_plus, ['populacja', 'długość', 'powDorzecza', 'średniPrzepływ', 'gęstość', 'powierzchnia']))

#Some predicates are too broad and it's necessary to specify we are only interested in entities of specific type.
type_restrictions = {
    quote_plus('długość'): 'Stream',
    quote_plus('gęstość'): 'PopulatedPlace',
    'powierzchnia': 'PopulatedPlace',
    'stan': 'Place',
}

sparql_endpoint = 'http://localhost:8890/sparql/'
articles_url = 'http://dumps.wikimedia.org/plwiki/20110802/plwiki-20110802-pages-articles.xml.bz2'
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
articles_cache_path = \
    cache_path + '%s/articles_spejd/%%s' % lang if use_parser and parser_type == 'spejd' \
    else cache_path + '%s/dep_articles/%%s' % lang if use_parser and parser_type == 'dependency' \
    else cache_path + '%s/articles/%%s' % lang
candidates_cache_path = cache_path + '%s/candidates/%%s' % lang
models_cache_path = cache_path + '%s/models/%%s' % lang
results_path = main_path + 'results/%s/' % lang
tests_path = main_path + 'tests/%s/' % lang
spejd_path = ext_path + 'spejd-1.3.6'
maltparser_path = ext_path + 'maltparser-1.7.1/'

def create_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)

#Check if dependencies are available
def check():
    #SPARQL server responds
    try:
        from sparql_access import count_entities_of_type
        count_entities_of_type([u'http://dbpedia.org/ontology/Settlement'])
    except ValueError:
        raise RuntimeError('Cannot access SPARQL endpoint: %s.' % sparql_endpoint)
    #raw articles are available
    create_dir(data_path)
    create_dir(raw_articles_path)
    if not os.listdir(raw_articles_path):
        #Wikipedia data archive is available
        try:
            from bz2 import BZ2File
            create_dir(wikidump_path)
            BZ2File(os.path.join(wikidump_path, articles_url.split('/')[-1]))
        except IOError:
            import urllib2
            print 'Downloading Wikipedia pages-articles archive.'
            try:
                u = urllib2.urlopen(articles_url)
            except urllib2.HTTPError:
                raise RuntimeError('Cannot download file: %s.' % articles_url)
            f = open(os.path.join(wikidump_path, articles_url.split('/')[-1]), 'wb')
            f.write(u.read())
            f.close()
            print 'Finished downloading.'
        import extract_dumps
        print 'Extracting raw articles from the archive.'
        extract_dumps.main()
        print 'Finished extracting.'
  
check()
