import os
import sys
from codecs import open as copen
from subprocess import Popen, PIPE
from itertools import izip

from config import models_cache_path, verbose, numeric_predicates
from language_tools import LanguageToolsFactory, is_numeric
from collect_entities import entities_types
from candidates_selector import CandidatesSelector

lt = LanguageToolsFactory.get_language_tools()

class ValueExtractor:
    def __init__(self, predicate, training_data, features):
        self.predicate = predicate
        self.most_informative_features = features
        self.predominant_types = map(
            lambda t: t.split('/')[-1], 
            CandidatesSelector.get_predominant_types(predicate, False)
        )
        self.model_filename = 'crfmodel'
        self.features_train_filename = 'features_train'
        self.features_tag_filename = 'features_tag'
        self.train(training_data)
        
    def extract_features(self, sentence, i):
        def recent_year(word):
            try:
                return 1990 <= int(word) <= 2012
            except ValueError:
                return False
            
        def other_year(word):
            try:
                return 1001 <= int(word) <= 1989
            except ValueError:
                return False
        
        lemma = sentence[i].lemma
        segment = sentence[i].segment
        lemmas = [word.lemma for word in sentence]
        features = {
            'segment': segment,
            'tag': sentence[i].tag,
            'lemma': lemma,
            'recent_year': str(int(recent_year(lemma))),
            'other_year': str(int(other_year(lemma))),
            'alldigits': str(int(lemma.isdigit())),
            'allalpha': str(int(lemma.decode('utf-8').isalpha())),
            'allcapitals': str(int(lemma.decode('utf-8').isupper())),
            'starts_with_capital': str(int(lemma.decode('utf-8')[0].isupper())),
            'segm_starts_with_capital': str(int(segment.decode('utf-8')[0].isupper())),
            'numeric': str(int(is_numeric(lemma)))
        }
        #note if window before and after contains one of the words deemed significant by the sentence classifier
        window_size = 3
        for feature in self.most_informative_features:
            features['%s_before' % feature] = str(int(feature in lemmas[max(0, i-window_size): i]))
            features['%s_after' % feature] = str(int(feature in lemmas[i+1: i+1+window_size]))
        window_size = 2
        for j in xrange(max(0, i - window_size), min(i + window_size + 1, len(sentence))):
            features['%d_lemma' % (j-i)] = lemmas[j]
        return features
        
    def save_features_to_file(self, filename, sentences, selected_values=None):
        f = copen(models_cache_path % filename, 'w', 'utf-8')
        for i, sentence in enumerate(sentences):
            for j, word in enumerate(sentence):
                if selected_values:
                    values = selected_values[i]
                    cls = int(any(word.lemma == value for value in values))
                    print >>f, '%d\t' % cls,
                for name, value in self.extract_features(sentence, j).iteritems():
                    print >>f, ('%s=%s\t' % (name, value)).decode('utf-8'),
                print >>f
            print >>f
        
    def train(self, training_data):
        sentences, selected_values = zip(*training_data)
        self.save_features_to_file(self.features_train_filename, sentences, selected_values)
        command = 'crfsuite learn -m %s %s' % (models_cache_path % self.model_filename, models_cache_path % self.features_train_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        p.communicate()

    def extract_values(self, sentences):
        print sentences
        self.save_features_to_file(self.features_tag_filename, sentences)
        command = 'crfsuite tag -i -m %s %s' % (models_cache_path % self.model_filename, models_cache_path % self.features_tag_filename)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        out, _ = p.communicate()
        tags_list = []
        tags = []
        for line in out.split('\n')[:-1]:
            if not line:
                tags_list.append(tags)
                tags = []
            else:
                tags.append((line[0], float(line[2:])))
        ret = []
        for sentence, tags in izip(sentences, tags_list):
            values = []
            value = []
            for word, (tag, p) in zip(sentence, tags) + [('', ('0', 1))]:
                #FIXME use probabilities
                if tag == '1':
                    value.append(word.lemma)
                else:
                    if value:
                        values.append('_'.join(value))
                        value = []
            if values:
                if self.predicate in numeric_predicates:
                    ret.append(values[0])
                    continue
                #to increase precision of extraction (at the cost of recall) in textual relations, 
                #only values that are geographic entities in DBPedia are returned
                values_identified_as_entities = [
                    v for v in values if lt.is_entity(v)
                ]
                values_identified_as_entities_of_right_type = [
                    v for v in values_identified_as_entities if\
                    any(entities_types.index(t) in lt.entities[v] for t in self.predominant_types)
                ]
                if verbose:
                    print 'Potential values:'
                    print ' '.join(values)
                    print ' '.join(values_identified_as_entities)
                    print ' '.join(values_identified_as_entities_of_right_type)
                    print
                if values_identified_as_entities_of_right_type:
                    ret.append(values_identified_as_entities_of_right_type[0])
                elif values_identified_as_entities:
                    ret.append(values_identified_as_entities[0])
                else:
                    ret.append(None)
            else:
                ret.append(None)
        return ret
                   
