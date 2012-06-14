import cPickle as pickle

class Pickler:
    @staticmethod
    def store(object, filename):
        pickle.dump(object, open(filename, 'wb'), -1)

    @staticmethod
    def load(filename):
        return pickle.load(open(filename, 'rb'))
