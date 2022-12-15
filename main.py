import logging, argparse

from torch import cosine_similarity
logger = logging.getLogger(__name__)

from flask import Flask, request
from text_preprocessing import get_corpus
from word_embedding import get_word_embedding
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
from scipy.spatial.distance import cosine
 
app = Flask(__name__)

from database_preprocessing import preprocess_database
db=preprocess_database()

def similarity_matching(preprocessed_user_message, word_embedding_database, default_reply_thres):
    """
    Match the user message and the candidate questions in database 
       to find the most similar question and answer along with the type of submodule 
    """
    user_message_embedding = get_word_embedding(preprocessed_user_message)
    max_similarity = 0
    max_question = ""
    max_answer = ""
    df=pd.read_csv("QnA.csv")
    for index,row in df.iterrows():
        question,answer=row
        # the cosine formula in scipy is [1 - (u.v / (||u||*||v||))]
        # so we have to add 1 - consine() to become the similary match instead of difference match 
        similarity = 1-cosine(user_message_embedding, db[question])
        if similarity > max_similarity:
            max_similarity, max_question, max_answer= similarity, question, answer


    logger.info("Highest Similarity Score: "+str(max_similarity))
    logger.info("Highest Confidence Level Question: "+str(max_question))
    logger.info("Highest Confidence Level Answer: "+str(max_answer))

    # if the highest similarity is lower the predefined threshold
    # default reply will be sent back to the user
    if max_similarity >= default_reply_thres:
        return max_answer
    else:
        return "Please rephrase your question."
 
@app.route("/wa")
def wa_hello():
    return "Hello, World!"
 
@app.route("/wasms", methods=['POST'])
def wa_sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    msg = request.form.get('Body').lower()  # Reading the messsage from the whatsapp
    logger.info("msg-->",msg)
    resp = MessagingResponse()
    reply=resp.message()
    preprocessed_text=get_corpus(msg)
    reply.body(similarity_matching(preprocessed_text,db,0.8))
    return str(resp)
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging', action='store_true')
    args = parser.parse_args()
    if args.logging:
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
    app.run(debug=True)