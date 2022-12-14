# Text Preprocessing
import nltk 
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Word Embedding
from transformers import BertTokenizer, BertModel
BertTokenizer.from_pretrained('bert-base-uncased')
BertModel.from_pretrained('bert-base-uncased',
                                output_hidden_states = True, # Whether the model returns all hidden-states.
                                )