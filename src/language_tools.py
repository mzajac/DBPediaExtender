#encoding: utf-8
import sys
from subprocess import Popen, PIPE
from os.path import join
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from string import digits, punctuation

opennlp_path = 'opennlp-tools-1.5.0'

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
        
    def convert_to_base_form(self, sentence):
        return [
            w.replace(',', '') for w in sentence
        ]
        
    def prepare_sentence(self, sentence):
        sentence = sentence.split()
        sentence = self.convert_to_base_form(sentence)
        return sentence
        
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
        
    def tokenize(self, text):
        if text is None:
            return None
        sentence_model = join(opennlp_path, 'en-sent.bin')
        tokens_model = join(opennlp_path, 'en-token.bin')
        command = './%s/bin/opennlp SentenceDetector %s | ./%s/bin/opennlp TokenizerME %s' % (opennlp_path, sentence_model, opennlp_path, tokens_model)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate(text)
        sentences = out.rstrip('\n').split('\n')
        return sentences

    def lemmatize(self, words):
        return map(lambda w: self.lemmatizer.stem_word(w), words)
        
    def remove_stop_words(self, words):
        return filter(lambda w: w.encode('utf8') not in self.stopwords, words)

class PolishTools(LanguageTools):
    pass
    
