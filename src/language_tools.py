#encoding: utf-8
import sys
import re
import glob
from subprocess import Popen, PIPE
from os.path import join
from string import digits, punctuation
from locale import atof, setlocale, LC_NUMERIC
import lxml.etree as etree
from collections import namedtuple

from config import lang, numeric_predicates, entities_path, raw_articles_path
from construct_synonym_set import get_synonyms
from pickler import Pickler

Word = namedtuple('Word', ['segment', 'lemma', 'tag'])

def extract_shortened_name(name):
    return re.split(',|\(', name.replace('_', ' '))[0]
    
def is_numeric(s):
    if s.lower() in ['infinity', 'nan']:
        return False
    try:
        atof(s)
        return True
    except ValueError:
        return False

class LanguageToolsFactory:
    @staticmethod
    def get_language_tools():
        if lang == 'pl':
            #set ',' as decimal character
            setlocale(LC_NUMERIC, '')
            return PolishTools()
        raise NotImplementedError()
        
class LanguageTools:
    def __init__(self):
        self.entities = Pickler.load(entities_path)
        self.synonyms = get_synonyms()
        
    def is_entity(self, segment):
        return segment in self.entities


class PolishTools(LanguageTools):
    def __init__(self):
        LanguageTools.__init__(self)

    def parse_disamb_file(self, f):
        article = []
        sentence = []
        for _, elem in etree.iterparse(f,  events=('end',)):
            if elem.tag == 'chunk' and elem.attrib['type'] == 's':
                article.append(sentence)
                sentence = []
            elif elem.tag == 'tok':
                segment = elem.getchildren()[0].text.encode('utf-8')
                for interp in elem.iterchildren():
                    if interp.tag == 'lex':
                        lemma = interp.getchildren()[0].text.encode('utf-8')
                        tag = interp.getchildren()[1].text.encode('utf-8')
                        if 'disamb_sh' not in interp.attrib:
                            break
                sentence.append(Word(segment, lemma, tag))
        return article
        
    def join_numerals(self, article):
        for j, sentence in enumerate(article):
            #join numerals ('3' ',' '5' becomes '3,5') and '100' '000' becomes '100000'
            i = 0
            while i < len(sentence) - 2:
                if is_numeric(sentence[i].lemma) and sentence[i+1].lemma in '.,' and is_numeric(sentence[i+2].lemma):
                    if sentence[i+1].lemma == '.':
                        new_lemma = sentence[i].lemma + sentence[i+2].lemma
                    else:
                        new_lemma = sentence[i].lemma + ',' + sentence[i+2].lemma
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag)
                    sentence = sentence[: i+1] + sentence[i+3 :]
                i += 1
            i = 0
            while i < len(sentence) - 1:
                if is_numeric(sentence[i].lemma) and is_numeric(sentence[i+1].lemma):
                    new_lemma = sentence[i].lemma + sentence[i+1].lemma
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag)
                    sentence = sentence[: i+1] + sentence[i+2 :]
                else:
                    i += 1
            #replace occurrences of 'tysiąc' and 'milion' with their numerical values
            #e.g. ('3,5' 'tys' becomes '3500')
            thousand = ['tysiąc', 'tys']
            million = ['mln', 'milion']
            i = 0
            while i < len(sentence) - 1:
                if is_numeric(sentence[i].lemma) and sentence[i+1].lemma in thousand + million:
                    product = 10**3 if sentence[i+1].lemma in thousand else 10**6
                    new_lemma = str(int(round(atof(sentence[i].lemma) * product)))
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag)
                    if i < len(sentence) - 2 and sentence[i+1].lemma == 'tys' and sentence[i+2].lemma == '.':
                        sentence = sentence[: i+1] + sentence[i+3 :]
                    else:
                        sentence = sentence[: i+1] + sentence[i+2 :]
                i += 1
            article[j] = sentence
        return article
        
    def prepare_article(self, article, link_dictionary):
        return self.join_numerals(article)
        
    def prepare_value(self, value, predicate):
        if predicate in numeric_predicates:
            product = 1000 if 'tys' in value else (10**6 if 'mln' in value else 1)
            #Population value may look '99 2001 Census'. We would like to strip the information about census.
            value = re.sub('\d{4} Census', '', value)
            #Population sometimes has year of census in parentheses - it should be stripped.
            value = value.split('(')[0]
            try:
                f = atof(filter(lambda c: c.isdigit() or c == ',', value))
                return [str(int(round(product * f)))]
            except ValueError:
                pass
        else:
            #in Polish DBPedia a picture is often a part of a value 
            #and it is saved as e.g. "20px Neapol" where "Neapol" is the right value
            value = re.sub('\dpx', '', value)
            value = filter(lambda c: not c.isdigit(), value)
        return value.split(' ')

    def run_tagger(self, link_dictionaries):
        '''runs pantera-tagger on all .txt files in raw_articles_path directory and then parses the results'''
        command = 'pantera --tagset nkjp -o xces %s/*.txt' % raw_articles_path
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        _, err = p.communicate()
        if 'ERROR' in err:
            raise Error('Pantera error:\n\n%s' % err)
        articles = {}
        for f in glob.glob('%s/*.disamb' % raw_articles_path):
            i = int(f[len(raw_articles_path)+1 : -len('.txt.disamg')])
            articles[i] = self.prepare_article(self.parse_disamb_file(f), link_dictionaries[i])
        sys.exit()
        return articles   

