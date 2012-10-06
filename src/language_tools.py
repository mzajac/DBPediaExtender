#encoding: utf-8
import sys
import re
from subprocess import Popen, PIPE
from os.path import join
from string import digits, punctuation

from config import entities_path
from construct_synonym_set import get_synonyms
from pickler import Pickler
            
def extract_shortened_name(name):
    return re.split(',|\(', name.replace('_', ' '))[0]
    
def is_numeric(s):
    if s.lower() in ['infinity', 'nan']:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False

class LanguageToolsFactory:
    @staticmethod
    def get_language_tools(lang):
        if lang == 'en':
            from config import stanford_path
            from nltk.stem.porter import PorterStemmer
            from nltk.corpus import stopwords
            return EnglishTools()
        if lang == 'pl':
            return PolishTools()
        raise NotImplementedError()
        
class LanguageTools:
    def __init__(self):
        self.entities = Pickler.load(entities_path)
        self.synonyms = get_synonyms()
        
    def remove_nonwords(self, sentence):
        return [
            w for w in sentence
            if all(c not in digits for c in w) and not all(c in punctuation for c in w) 
        ]
        
    def convert_numerals_to_base_form(self, sentence):
        '''converts numerals to base form e.g. 100,000 becomes 100000'''
        return [
            w.replace(',', '') if w != ',' else w for w in sentence 
        ]
        
    def convert_floats_to_integers(self, sentence):
        print sentence
        return [
            str(int(round(float(w)))) if is_numeric(w) else w for w in sentence 
        ]
        
    def extract_vector_of_words(self, sentence):
        sentence = map(lambda w: w.decode('utf8').lower(), sentence)
        sentence = self.remove_nonwords(sentence)
        sentence = self.remove_stop_words(sentence)
        sentence = self.lemmatize(sentence)
        return sentence
        
    def replace_synonyms(self, sentence):
        for i, segment in enumerate(sentence):
            if segment in self.synonyms:
                sentence[i] = self.synonyms[segment][0]
        return sentence
        
    def join_locations(self, sentence, locations):
        new_sentence = []
        i = 0
        while i < len(sentence):
            if sentence[i] not in locations:
                new_sentence.append(sentence[i])
                i += 1
            else:
                start = i
                while sentence[i] in locations:
                    i += 1
                new_sentence.append('_'.join(sentence[start : i]))
        return new_sentence
        
    def join_entities(self, sentence, max_entity_len=7):
        def construct_entity(segments):
            ret = ''
            for i, segment in enumerate(segments):
                last_segment = '' if i == 0 else segments[i-1]
                if segment in ',)' or last_segment == '(' or not ret:
                    ret += segment
                else:
                    ret += ' ' + segment
            return ret
        
        length = 2
        while length < max_entity_len:
            for i in xrange(len(sentence) - length + 1):
                possible_entity = construct_entity(sentence[i : i+length])
                if self.is_entity(possible_entity):
                    sentence[i] = possible_entity.replace(' ', '_')
                    del sentence[i+1 : i+length]
                    break
            else:
                length += 1
        return sentence

    def join_segments_constituting_en_entity(self, sentence, locations=None):
        return self.join_entities(sentence)
        
    def is_entity(self, segment):
        return segment in self.entities
        

class EnglishTools(LanguageTools):
    def __init__(self):
        LanguageTools.__init__(self)
        self.lemmatizer = PorterStemmer()
        self.stopwords = set(stopwords.words('english'))
        
    def split(self, segments, sentence_ending_segments='.!?'):
        sentences = []
        sentence = []
        for segment in segments:
            sentence.append(segment)
            if segment in sentence_ending_segments:
                sentences.append(sentence)
                sentence = []
        return sentences
        
    def tokenize(self, texts):
        #to improve tokenizer performance all texts are combined into one text separated by a special character
        #then output is separated again based on occurence of that character
        separator_character = '~'
        #beforehand I remove all occurences of the separator
        texts = map(lambda text: text.replace(separator_character, ''), texts)
        text = (' %s ' % separator_character).join(texts)
        command = 'java -cp %s/stanford-parser.jar edu.stanford.nlp.process.PTBTokenizer -options "normalizeParentheses=false"' % stanford_path
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate(text)
        texts = out.split(separator_character)
        tokenized_texts = []
        for text in texts:
            sentences = self.split(text.split('\n'))
            if sentences[-1] == ['']:
                sentences.pop()
            sentences = map(lambda s: filter(lambda w: w, s), sentences)
            sentences = filter(lambda s: s, sentences)
            sentences = map(lambda s: self.convert_numerals_to_base_form(s), sentences)
            sentences = map(lambda s: self.convert_floats_to_integers(s), sentences)
            sentences = map(lambda s: self.join_segments_constituting_en_entity(s), sentences)
            sentences = map(lambda s: self.replace_synonyms(s), sentences)
            tokenized_texts.append(sentences)
        return tokenized_texts
                
    def lemmatize(self, words):
        return map(lambda w: self.lemmatizer.stem_word(w), words)
        
    def remove_stop_words(self, words):
        return filter(lambda w: w.encode('utf8') not in self.stopwords, words)
        

class PolishTools(LanguageTools):
    def tokenize(self, texts):
        tokenized_texts = []
        for text in texts:
            text = text.replace('|', '')
            command = 'toki-app -q -f "\$bs|\$orth "'
            p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
            out, _ = p.communicate(text)
            sentences = out.split('|')
            sentences = map(lambda s: s.split(), sentences)
            sentences = filter(lambda s: s, sentences)
            sentences = map(lambda s: self.convert_numerals_to_base_form(s), sentences)
            sentences = map(lambda s: self.convert_floats_to_integers(s), sentences)
#            sentences = map(lambda s: self.join_segments_constituting_en_entity(s), sentences)
#            sentences = map(lambda s: self.replace_synonyms(s), sentences)
            tokenized_texts.append(sentences)
        return tokenized_texts
        
    def lemmatize(self, words):
        return words
        
    def remove_stop_words(self, words):
        return words


