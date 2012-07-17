#encoding: utf-8
import sys
from subprocess import Popen, PIPE
from os.path import join
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from string import digits, punctuation

from config import stanford_path, anchor_sign

class Segment(str):
    def __init__(self, s):
        self.is_anchor = False
        self = s

class LanguageToolsFactory:
    @staticmethod
    def get_language_tools(lang):
        if lang == 'en':
            return EnglishTools()
        if lang == 'pl':
            return PolishTools()
        raise NotImplementedError()
        
class LanguageTools:
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
        
    def extract_vector_of_words(self, sentence):
        sentence = map(lambda w: w.decode('utf8').lower(), sentence)
        sentence = self.remove_nonwords(sentence)
        sentence = self.remove_stop_words(sentence)
        sentence = self.lemmatize(sentence)
        return sentence

class EnglishTools(LanguageTools):
    def __init__(self):
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
        
    def save_anchors_info(self, sentence):
        new_sentence = []
        for segment in sentence:
            if segment == anchor_sign:
                if new_sentence:
                    new_sentence[-1].is_anchor = True
            else:
                new_sentence.append(Segment(segment))
        return new_sentence
        
    def tokenize(self, text):
        if text is None:
            return None
        command = 'java -cp %s/stanford-parser.jar edu.stanford.nlp.process.PTBTokenizer -options "normalizeParentheses=false"' % stanford_path
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate(text)
        sentences = self.split(out.split('\n'))
        if sentences[-1] == ['']:
            sentences.pop()
        sentences = map(lambda s: filter(lambda w: w, s), sentences)
        sentences = map(lambda s: self.convert_numerals_to_base_form(s), sentences)
        sentences = map(lambda s: self.save_anchors_info(s), sentences)
        return sentences

    def lemmatize(self, words):
        return map(lambda w: self.lemmatizer.stem_word(w), words)
        
    def remove_stop_words(self, words):
        return filter(lambda w: w.encode('utf8') not in self.stopwords, words)

class PolishTools(LanguageTools):
    pass
    
