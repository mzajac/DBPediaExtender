# -*- coding: utf-8 -*-

from __future__ import division
from itertools import izip

from sentence_classifier import get_sentence_classifier
from candidates_selector import CandidatesSelector

class Stats:
    def __init__(self, tp, fp, fn):
        self.tp, self.fp, self.fn = tp, fp, fn
        
    def __repr__(self):
        self.calculate_statistics()
        return 'precision:%.2f recall:%.2f F-measure:%.2f all:%d' % (self.precision, self.recall, self.f_measure, self.tp + self.fn)

    def calculate_statistics(self):
        self.precision = self.tp / max(self.tp + self.fp, 1)
        self.recall = self.tp / max(self.tp + self.fn, 1)
        self.f_measure = 2 * self.precision * self.recall / (self.precision + self.recall) if self.precision != 0 else 0
        
class Evaluator:
    @staticmethod
    def evaluate(true_values, entities, sentences):
        def value_matches():
            if type(true_values[e]) == list:
                return any(str(v) in s for v in true_values[e])
            return str(true_values[e]) in s
        
        tp, fp, fn = 0, 0, 0
        for e, s in izip(entities, sentences):
            if e in true_values and value_matches():
                tp += 1
            else:
                fp += 1
        fn = len(true_values) - tp
        print Stats(tp, fp, fn)
    
def populationEnglishTest():
    predicate = 'populationTotal'
    entities = ['Dete', 'Codpa', 'Ebenfurth', 'Felixdorf', 'Arborfield', 'Hirtenberg', 'Falkenfels', 'Mauerstetten', 'Osterzell', 'W\xc3\xb6rth_an_der_Donau', 'Eugendorf', 'Vilsbiburg', 'Titisee-Neustadt', 'Patersdorf', 'New_Eltham', 'Hainsfarth', 'Riedenburg', 'Ruhmannsfelden', 'Germaringen', 'Besigheim', 'Chislehurst', 'Eggenthal', 'Back,_Lewis', 'Steenderen', 'Kungsbacka_Municipality', 'Napoleon,_Michigan', 'Blandinsville,_Illinois', 'Bellflower,_Illinois', 'Bardolph,_Illinois', 'Metropolis,_Illinois', 'Alexis,_Illinois', 'Cavendish,_Suffolk', 'Tremont,_Maine', 'Anfield,_Liverpool', 'Angel_City,_Florida', 'Century_City,_Cape_Town', 'Gorman,_California', 'Cubley,_South_Yorkshire', 'Boeng_Pring', 'Empire,_Mendocino_County,_California', 'Robinson,_California', 'Halo,_West_Virginia', 'Nason,_Illinois', 'Buch,_Rhein-Lahn', 'Venhuizen', 'Kirby,_Wisconsin', 'Finsp\xc3\xa5ng_Municipality', 'Str\xc3\xa4ngn\xc3\xa4s_Municipality', 'Kinda_Municipality', 'S\xc3\xa4ffle_Municipality', 'Arvika_Municipality', 'Arjeplog_Municipality', 'V\xc3\xa4xj\xc3\xb6_Municipality', 'Tingsryd_Municipality', 'Lessebo_Municipality', 'Gaoyao', 'Oatman,_Arizona', 'Lax\xc3\xa5_Municipality', 'Nora_Municipality', '\xc3\x96rebro_Municipality', 'Rockwood,_Maine', 'Harding,_KwaZulu-Natal', 'Ivindo_Department', 'Barham,_Huntingdonshire', 'Hereford,_Maryland', 'Hereford,_Colorado', 'Sankt_Jakob_in_Haus', 'Cornell,_California', 'K\xc3\xb6ping_Municipality', 'Hallstahammar_Municipality', 'Pf\xc3\xa4ffikon_District', 'Pf\xc3\xa4ffikon,_Zurich', 'Dass,_Nigeria', 'Bigfork,_Minnesota', 'Moores_Flat,_California', 'Ruda,_Gmina_Przy\xc5\x82\xc4\x99k', 'Ruda,_Ostr\xc3\xb3w_Mazowiecka_County', 'Gnesta_Municipality', 'Castletownbere', 'Ballyheigue', 'Bournville', 'Lakenheath', 'Selly_Oak', 'Burry_Port', 'Breadstone', 'East_Hanningfield', 'Pampisford', 'Haversham', 'Horseheath', 'Ambatofinandrahana', 'Baltasound', 'Somerleyton', 'St_Olaves', 'Beryl,_Utah', 'Cornforth', 'Tallentire', 'Birnin_Kudu', 'Bornu_Yassa', 'Titiwa', 'Koulen']
    true_values = {
        'Hirtenberg': 2500,
        'Mauerstetten': 2800,
        'Eugendorf': 6439,
        'Vilsbiburg': 11000,
        'Napoleon,_Michigan': 1254,
        'Blandinsville,_Illinois': 777,
        'Bellflower,_Illinois': 408,
        'Bardolph,_Illinois': 253,
        'Metropolis,_Illinois': 6482,
        'Alexis,_Illinois': 863,
        'Tremont,_Maine': 1529,
        'Nason,_Illinois': 234,
        'Venhuizen': 7812,
        'Gaoyao': 706000,
        'Oatman,_Arizona': 128,
        'Sankt_Jakob_in_Haus': 656,
        'Pfäffikon,_Zurich': 10817,
        'Dass,_Nigeria': 89943,
        'Bigfork,_Minnesota': 446,
        'Castletownbere': 875,
        'Ballyheigue': 2031,
        'Bournville': 25462,
        'Lakenheath': 8200,
        'Selly_Oak': 25792,
        'Burry_Port': [8000, 4209], #both values are reasonable
        'Haversham': 803,
        'Birnin_Kudu': 27000,
        'Bornu_Yassa': 5987,
    }
    sc = get_sentence_classifier(predicate)
    entities, sentences = sc.extract_sentences(entities)
    Evaluator.evaluate(true_values, entities, sentences)
    
def run_evaluation():
    populationEnglishTest()
