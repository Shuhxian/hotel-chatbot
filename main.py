import logging, argparse

from torch import cosine_similarity
logger = logging.getLogger(__name__)

from flask import Flask, request
from text_preprocessing import get_corpus
from word_embedding import get_word_embedding
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
from scipy.spatial.distance import cosine
from database import create_db, get_facilities,get_nearby_restaurants,get_nearby_attractions,get_availability,get_booking_details,make_booking,cancel_booking, get_room_types
import datetime

app = Flask(__name__)
dbname="hotel_chatbot"

curr_question=""
responses=[]

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
        return max_question,max_answer
    else:
        return None,"Sorry, I do not understand what you are saying. Please rephrase your question."
 
@app.route("/wa")
def wa_hello():
    return "Hello, World!"
 
@app.route("/wasms", methods=['POST'])
def wa_sms_reply():
    global curr_question, responses
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    msg = request.form.get('Body')  # Reading the messsage from the whatsapp
    logger.info("msg-->",msg)
    resp = MessagingResponse()
    reply=resp.message()
    if msg=="Restart chat":
        reply.body("Chat restarted")
        curr_question=""
        responses=[]
        return str(resp)
    if not curr_question:
        preprocessed_text=get_corpus(msg)
        curr_question, ans=similarity_matching(preprocessed_text,db,0.8)
        if curr_question=="What facilities do you have?":
            ans="Our facilities include:\n"
            facilities=get_facilities()
            if not facilities:
                ans="We do not offer any facilities."
            for i in range(len(facilities)):
                ans+="{}. {}\n".format(i+1,facilities[i])
        elif curr_question=="What are the type of rooms that you offer?":
            ans="We provide these types of rooms:\n"
            room_types=get_room_types(dbname)
            if not room_types:
                ans="We do not offer any rooms."
            for i in range(len(room_types)):
                ans+="{}. {}\n".format(i+1,room_types[i])
        elif curr_question=="What are some of the restaurants nearby?":
            random_restaurant=get_nearby_restaurants()
            if not random_restaurant:
                ans="We do not have any recommended restaurants nearby."
            else:
                ans="We would recommend you to check out {}.".format(random_restaurant)
        elif curr_question=="What are some of the attractions nearby?":
            random_attraction=get_nearby_attractions()
            if not random_attraction:
                ans="We do not have any recommended attractions nearby."
            else:
                ans="We would recommend you to check out {}.".format(random_attraction)
        elif curr_question=="I would like to make a reservation.":
            responses.append("Make")
            curr_question="Please provide the starting date in the format YYYY-MM-DD."
            ans=curr_question
        elif curr_question=="I would like to check for room availability.":
            responses.append("Check")
            curr_question="Please provide the starting date in the format YYYY-MM-DD."
            ans=curr_question
        elif curr_question=="I would like to cancel a reservation.":
            responses.append("Cancel")
            curr_question="Please provide me the booking ID."
            ans=curr_question
        elif curr_question=="I would like to check a reservation.":
            responses.append("Check")
            curr_question="Please provide me the booking ID."
            ans=curr_question
        if curr_question in ["What facilities do you have?","What are some of the restaurants nearby?", "What are the type of rooms that you offer?", \
            "What are some of the attractions nearby?","Do you provide parking space?","How do I contact you?"]:
            curr_question=""
    else:
        #Sub-question
        if curr_question=="Please provide the starting date in the format YYYY-MM-DD.":
            try:
                datetime.datetime.strptime(msg,'%Y-%m-%d')
                responses.append(msg)
                curr_question="Please provide the ending date in the format YYYY-MM-DD."
                ans=curr_question
            except:
                ans="Date format invalid. Please try again."
        elif curr_question=="Please provide the ending date in the format YYYY-MM-DD.":
            try:
                datetime.datetime.strptime(msg,'%Y-%m-%d')
                responses.append(msg)
                curr_question="Please provide the desired room type."
                ans=curr_question
            except:
                ans="Date format invalid. Please try again."
        elif curr_question=="Please provide the desired room type.":
            type_check=True
            if "single" in msg.lower():
                room="Single"
            elif "deluxe" in msg.lower():
                room="Deluxe"
            else:
                ans="Sorry, we only provide Single and Deluxe rooms."
                responses=[]
                curr_question=""
            if type_check:
                if responses[0]=="Make":
                    id=make_booking(dbname,responses[1],responses[2],room)
                    if id:
                        ans="Booking successful. Your booking ID is {}.".format(id)
                        responses=[]
                        curr_question=""
                    else:
                        ans="Sorry, the desired room type is full for the specified date. Please try with other dates."
                        responses=[]
                        curr_question=""
                else:
                    if get_availability(dbname,responses[1],responses[2],room)>0:
                        ans="Yes, there are rooms available."
                        responses=[]
                        curr_question=""
                    else:
                        ans="Sorry, the desired room type is full for the specified date. Please try with other dates."
                        responses=[]
                        curr_question=""
        elif curr_question=="Please provide me the booking ID.":
            if responses[0]=="Check":
                start_date,end_date,room_id,room_type,price=get_booking_details(dbname,msg)
                if not start_date:
                    ans="The booking ID does not exist. Please check again."
                    responses=[]
                    curr_question=""
                else:
                    ans="Your booking details are as follow:\nCheck In Date: {}\nCheck Out Date: {}\nRoom Type: {}\nPrice: {}".format(start_date,end_date,room_type,price)
                    responses=[]
                    curr_question=""
            else:
                if cancel_booking(dbname,msg):
                    ans="Booking  {} cancelled.".format(msg)
                    responses=[]
                    curr_question=""
                else:
                    ans="Booking  {} does not exist.".format(msg)
                    responses=[]
                    curr_question=""
    reply.body(ans)
    return str(resp)
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging', action='store_true')
    args = parser.parse_args()
    if args.logging:
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
    create_db()
    app.run(debug=True)