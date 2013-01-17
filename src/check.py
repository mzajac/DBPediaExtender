import os

from config import *

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
  
