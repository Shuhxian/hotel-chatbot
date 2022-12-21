import pandas as pd
from text_preprocessing import get_corpus
from word_embedding import get_word_embedding

def preprocess_database():
    """
    To return a preprocessed version of questions in the database
    """
    df=pd.read_csv("QnA.csv")
    processed_database={}
    for _,row in df.iterrows():
        question, answer=row
        processed_database[question] = get_word_embedding(get_corpus(question))
    return processed_database

if __name__=="__main__":
    from text_preprocessing import get_corpus
    preprocess_database(get_corpus(input()))