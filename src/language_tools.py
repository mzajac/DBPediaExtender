#encoding: utf-8
import sys
import os
import re
import glob
from subprocess import Popen, PIPE
from os.path import join
from os import chdir, getcwd
from string import digits, punctuation
from locale import atof, setlocale, LC_NUMERIC
import lxml.etree as etree
from collections import namedtuple

from config import lang, numeric_predicates, entities_path, raw_articles_path, verbose, spejd_path, use_parser, parser_type, maltparser_path, use_wordnet
from pickler import Pickler
from polish_stop_words import stop_words
from collect_entities import collect_entities

if use_wordnet:
    from nltk.corpus import wordnet as wn
stop_words = set(stop_words)
Word = namedtuple('Word', ['segment', 'lemma', 'tag', 'parse'])
article_sentence_limit = 10
#set ',' as decimal character

def is_numeric(s):
    if s.lower() in ['infinity', 'nan']:
        return False
    try:
        setlocale(LC_NUMERIC, 'pl_PL.UTF-8')
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
        self.entities = collect_entities()
        
    def is_entity(self, segment):
        return segment in self.entities


class PolishTools(LanguageTools):
    def __init__(self):
        LanguageTools.__init__(self)

    def parse_disamb_file(self, f):
        article = []
        sentence = []
        for _, elem in etree.iterparse(f):
            if elem.tag == 'chunk' and elem.attrib['type'] == 's':
                article.append(sentence)
                sentence = []
            elif elem.tag == 'tok':
                segment = elem.getchildren()[0].text.encode('utf-8')
                #default lemma and tag
                lemma = segment
                tag = 'ign'
                for interp in elem.iterchildren():
                    if interp.tag == 'lex' and 'disamb' in interp.attrib:
                        lemma = interp.getchildren()[0].text.encode('utf-8')
                        tag = interp.getchildren()[1].text.encode('utf-8')
                        break
                sentence.append(Word(segment, lemma, tag, ''))
        return article
        
    def parse_spejd_file(self, f):
        article = []
        sentence = []
        group_type_stack = []
        for event, elem in etree.iterparse(f, events=('start', 'end')):
            if elem.tag == 'group':
                if event == 'start':
                    group_type_stack.append(elem.attrib['type'])
                else:
                    group_type_stack.pop()
            if event == 'start':
                continue
            if elem.tag == 'chunk' and elem.attrib['type'] == 's':
                article.append(sentence)
                sentence = []
            elif elem.tag == 'tok':
                segment = elem.getchildren()[0].text.encode('utf-8')
                #default lemma and tag
                lemma = segment
                tag = 'ign'
                for interp in elem.iterchildren():
                    if interp.tag == 'lex' and 'disamb' in interp.attrib:
                        lemma = interp.getchildren()[0].text.encode('utf-8')
                        tag = interp.getchildren()[1].text.encode('utf-8')
                        break
                sentence.append(Word(segment, lemma, tag, group_type_stack[-1] if group_type_stack else ''))
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
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag, '')
                    sentence = sentence[: i+1] + sentence[i+3 :]
                i += 1
            i = 0
            while i < len(sentence) - 1:
                if is_numeric(sentence[i].lemma) and is_numeric(sentence[i+1].lemma):
                    new_lemma = sentence[i].lemma + sentence[i+1].lemma
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag, '')
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
                    sentence[i] = Word(new_lemma, new_lemma, sentence[i].tag, '')
                    if i < len(sentence) - 2 and sentence[i+1].lemma == 'tys' and sentence[i+2].lemma == '.':
                        sentence = sentence[: i+1] + sentence[i+3 :]
                    else:
                        sentence = sentence[: i+1] + sentence[i+2 :]
                i += 1
            article[j] = sentence
        return article
        
    def correct_lemmas(self, article, link_dictionary):
        '''Corrects lemmatization by using Wikipedia anchor links and some predefined rules.'''
        for i, sentence in enumerate(article):
            for j, word in enumerate(sentence):
                if word.segment in link_dictionary:
                    lemma_suggested_by_link = link_dictionary[word.segment]
                    if word.lemma != lemma_suggested_by_link:
                        article[i][j] = Word(word.segment, lemma_suggested_by_link, word.tag, word.parse)
                if article[i][j].lemma == 'Województwo':
                     article[i][j] = Word(word.segment, 'województwo', word.tag, word.parse)
        for i, sentence in enumerate(article):
            for j, word in enumerate(sentence):
                #if word is in capital letters not at the beginning of a sentence, lemma should also be in capital letters
                if j > 0 and word.segment.decode('utf-8')[0].isupper() and word.lemma.decode('utf-8')[0].islower():
                    article[i][j] = Word(word.segment, word.segment, word.tag, word.parse)
        return article
        
    def prepare_article(self, article, link_dictionary):
        link_dictionary = {
            k.encode('utf-8'): v.encode('utf-8')
            for k, v in link_dictionary.iteritems()
        }
        return self.join_numerals(
            self.correct_lemmas(article, link_dictionary)
        )
        
    def prepare_value(self, value, predicate):
        if predicate in numeric_predicates:
            product = 1000 if 'tys' in value else (10**6 if 'mln' in value else 1)
            #Population value may look '99 2001 Census'. We would like to strip the information about census.
            value = re.sub('\d{4} Census', '', value)
            #Sometimes additional information is provided - it should be stripped.
            v = []
            for c in value:
                if c not in '., ' and not c.isdigit():
                    if v:                
                        break
                else:
                    v.append(c)
            value = ''.join(v)
            try:
                f = atof(filter(lambda c: c.isdigit() or c == ',', value))
                return [str(int(product * f))]
            except ValueError:
                pass
            value = value.split(' ')
            for v in value:
                try:
                    f = atof(v)
                    return [str(int(f))]
                except ValueError:
                    pass
            return []
        else:
            #in Polish DBPedia a picture is often a part of a value 
            #and it is saved as e.g. "20px Neapol" where "Neapol" is the right value
            value = re.sub('\dpx', '', value)
            try:
                value = value.decode('utf-8')
            except UnicodeEncodeError:
                pass
            values = ''.join((c if c.isalpha() else ' ') for c in value).split()
            if len(values) > 1:
                values.append(value)
            values = map(lambda v: v.encode('utf-8'), values)
            values = filter(lambda v: len(v) > 1 and v not in stop_words, values)
            values = filter(lambda v: v not in ['rzeka', 'potok', 'miasto', 'wieś'], values)
            return values
        
    def run_nlptools(self, link_dictionaries):
        if use_parser:
            if parser_type == 'shallow':
                self.run_tagger()
                return self.run_spejd(link_dictionaries)
            elif parser_type == 'dependency':
                return self.run_dependency_parser(self.run_tagger(link_dictionaries))
            raise RuntimeError('Parser type unknown.')
        return self.run_tagger(link_dictionaries)

    def run_tagger(self, link_dictionaries=None):
        '''runs pantera-tagger on all .txt files in raw_articles_path directory and then parses the results'''
        command = 'pantera --skip-done --tagset nkjp -o xces-disamb %s/*.txt' % raw_articles_path
        #Pantera tagger sometimes segmfaults in seemingly random places.
        #Being unable to find the cause, I simply call it again, until it finishes without errors.
        while True:
            p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
            _, err = p.communicate()
            if 'All done' in err:
                break
        #if link dictionaries were not provided, don't save the articles yet, only after running the parser
        if link_dictionaries is None:
            return
        articles = {}
        for f in glob.glob('%s/*.disamb' % raw_articles_path):
            try:
                i = int(f[len(raw_articles_path)+1 : -len('.txt.disamg')])
                articles[i] = self.prepare_article(self.parse_disamb_file(f), link_dictionaries[i])
            except ValueError:
                continue
        return articles
        
    def run_spejd(self, link_dictionaries):
        command = 'spejd %s' % raw_articles_path
        old_path = getcwd()
        chdir(spejd_path)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        p.communicate()
        chdir(old_path)
        articles = {}
        for f in glob.glob('%s/*.spejd' % raw_articles_path):
            try:
                i = int(f[len(raw_articles_path)+1 : -len('.txt.spejd')])
                articles[i] = self.prepare_article(self.parse_spejd_file(f), link_dictionaries[i])
            except ValueError:
                continue
        return articles
        
    def run_dependency_parser(self, articles):
        model_filename = 'skladnica_liblinear_stackeager_final.mco'
        input_filename = 'i.conll'
        output_filename = 'o.conll'
        command = 'java -jar maltparser-1.7.1.jar -c %s -i %s -o %s -m parse' % (model_filename, input_filename, output_filename)
        old_path = getcwd()
        chdir(maltparser_path)
        self.save_conll_format(articles, input_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        p.communicate()
        self.read_conll_format(articles, output_filename)
        os.remove(input_filename)
        os.remove(output_filename)
        chdir(old_path)
        return articles
        
    def save_conll_format(self, articles, filename):
        with open(filename, 'w') as f:
            for article in articles.itervalues():
                for sentence in article:
                    for i, word in enumerate(sentence):
                        print >>f, '\t'.join([
                            str(i+1),
                            word.segment,
                            word.lemma,
                            self.get_tag(word.tag),
                            self.get_tag(word.tag),
                            self.get_morph_features(word.tag)
                        ])
                    print >>f
                
    def read_conll_format(self, articles, filename):
        i, j, k = 0, 0, 0
        values = list(articles.keys())
        with open(filename) as f:
            for line in f:
                if line == '\n':
                    j += 1
                    k = 0
                    continue
                line = line.split('\t')
                index = values[i]
                while j == len(articles[index]):
                    i += 1
                    j = 0
                    index = values[i]
                word = articles[index][j][k]
                articles[index][j][k] = Word(word.segment, word.lemma, word.tag, line[7])
                k += 1
        
    def get_simple_tag(self, tag):
        if tag.startswith('subst:'):
            return 'n'
        elif tag.startswith('adj:'):
            return 'a'
        elif tag.startswith('adv:'):
            return 'r'
        elif tag.startswith('fin:') or tag.startswith('praet:'):
            return 'v'
            
    def get_morph_features(self, tag):
        features = tag.split(':')[1:]
        return '|'.join(features) if features else '_'
        
    def get_tag(self, tag):
        return tag.split(':')[0]
        
    def get_gender(self, tag):
        return tag.split(':')[3] if self.get_simple_tag(tag) in ['a', 'n'] else ''
        
    def get_case(self, tag):
        return tag.split(':')[2] if self.get_simple_tag(tag) in ['a', 'n'] else ''
        
    def get_person(self, tag):
        return tag.split(':')[2] if self.get_simple_tag(tag) == 'v' else ''
        
    def get_number(self, tag):
        return tag.split(':')[1] if self.get_simple_tag(tag) in ['a', 'n', 'v'] else ''
        
    def get_aspect(self, tag):
        return tag.split(':')[3] if self.get_simple_tag(tag) == 'v' else ''
        
    def get_hypernym(self, word, level=1):
        def hypernyms(synsets, level):
            if level == 0:
                return []
            ret = []
            for synset in synsets:
                hyper = synset.hypernyms()
                ret += hyper + hypernyms(hyper, level - 1)
            return ret
    
        if not use_wordnet:
            return []
        simple_tag = self.get_simple_tag(word.tag)

        if simple_tag:
            synsets = wn.synsets(word.lemma, simple_tag)
        else:
            synsets = wn.synsets(word.lemma)
        return map(lambda s: s.name, synsets)[0]

#assert PolishTools().prepare_value('ok. 34,5 km', 'd%C5%82ugo%C5%9B%C4%87')[0] == '34'
#assert PolishTools().prepare_value('12,1 tys.', 'populacja')[0] == '12100'
#assert PolishTools().prepare_value('0,9 mln.', 'populacja')[0] == '900000'
#assert PolishTools().prepare_value('warmińsko-mazurskie', 'stolica') == ['warmińsko', 'mazurskie', 'warmińsko-mazurskie']
#assert is_numeric('50,3')
