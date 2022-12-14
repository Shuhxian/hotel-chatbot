import string
import nltk
import contractions
import numpy as np

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

def replace_contractions(text):
    """Replace contractions in string of text"""
    return contractions.fix(text)

def sent_to_words(text):
    return(nltk.word_tokenize(text))

def to_lowercase(words):
    """Convert all characters to lowercase from list of tokenized words"""
    return [word.lower() for word in words]

def remove_punctuation(words):
    """Remove punctuation from list of tokenized words"""
    table = str.maketrans('', '', string.punctuation)
    return [w.translate(table) for w in words]

def remove_stopwords(words):
    """Remove stop words from list of tokenized words"""
    return [word for word in words if not word in stopwords.words('english')]
    
def lemmatization(words):
    """Lemmatize verbs in list of tokenized words"""
    lemmatizer = WordNetLemmatizer()
    return [(lemmatizer.lemmatize(word, pos='v')) for word in words]
   
def get_corpus (data):
  text=replace_contractions(data)
  data_words = sent_to_words(text)
  data_words = to_lowercase(data_words)
  data_words = remove_punctuation(data_words) 
  data_words_nostops = remove_stopwords(data_words)
  data_lemmatized = lemmatization(data_words_nostops)   
  output = [string for string in data_lemmatized if string != ""]
  op=np.asarray(output)
  return op

if __name__=="__main__":
    print(get_corpus(input()))
