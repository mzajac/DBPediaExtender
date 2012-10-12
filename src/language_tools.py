#encoding: utf-8
import sys
import re
import glob
from subprocess import Popen, PIPE
from os.path import join
from string import digits, punctuation
from locale import atof
import lxml.etree as etree
from collections import namedtuple

from config import lang, entities_path, raw_articles_path
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
            return PolishTools()
        raise NotImplementedError()
        
class LanguageTools:
    def __init__(self):
        self.entities = Pickler.load(entities_path)
        self.synonyms = get_synonyms()
        
    def join_entities(self, article, max_entity_len=7):
        def construct_entity(words):
            ret = ''
            for i, word in enumerate(words):
                last_word = '' if i == 0 else words[i-1]
                if word in ',)' or last_word == '(' or not ret:
                    ret += word
                else:
                    ret += '_' + word
            return ret
        
        for sentence in article:
            length = 2
            while length < max_entity_len:
                for i in xrange(len(sentence) - length + 1):
                    lemmas = [word.lemma for word in sentence[i : i+length]]
                    possible_entity = construct_entity(lemmas).title()
                    if self.is_entity(possible_entity):
                        segments = [word.segment for word in sentence[i : i+length]]
                        sentence[i] = Word(construct_entity(segments), possible_entity, sentence[i].tag)
                        del sentence[i+1 : i+length]
                        break
                else:
                    length += 1
        return article
        
    def is_entity(self, segment):
        return segment in self.entities


class PolishTools(LanguageTools):
    def __init__(self):
        LanguageTools.__init__(self)
        from polish_stop_words import stop_words
        self.stopwords = set(stop_words)

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
        for sentence in article:
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
        return article
        
    def prepare_article(self, article):
        return self.join_entities(self.join_numerals(article))

    def run_tagger(self):
        '''runs pantera-tagger on all .txt files in raw_articles_path directory and then parses the results'''
        command = 'pantera --tagset nkjp -o xces %s/*.txt' % raw_articles_path
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        _, err = p.communicate()
        if 'ERROR' in err:
            raise Error('Pantera error:\n\n%s' % err)
        articles = {}
        for f in glob.glob('%s/*.disamb' % raw_articles_path):
            i = int(f[len(raw_articles_path)+1 : -len('.txt.disamg')])
            articles[i] = self.prepare_article(self.parse_disamb_file(f))
        return articles   


