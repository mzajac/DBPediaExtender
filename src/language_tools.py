#encoding: utf-8
import sys
from subprocess import Popen, PIPE
from os.path import join
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from string import digits, punctuation

from config import stanford_path

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
            tokenized_texts.append(sentences)
        return tokenized_texts

    def lemmatize(self, words):
        return map(lambda w: self.lemmatizer.stem_word(w), words)
        
    def remove_stop_words(self, words):
        return filter(lambda w: w.encode('utf8') not in self.stopwords, words)

class PolishTools(LanguageTools):
    pass
    
