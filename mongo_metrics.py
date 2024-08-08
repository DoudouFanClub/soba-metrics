import os
import json
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, timedelta

class MongoMetrics :
    def __init__(self, mongo_uri='mongodb://localhost:27017/'):
        self.client = MongoClient(mongo_uri)


    def retrieve_user_metrics(self, database='ConversationData'):
        db = self.client[database]

        user_list = self.retrieve_user_list(db)

        user_convo_details = {}
        for user in user_list:
            collection = db[user]

            # Retrieve Conversation List (Documents)
            convo_list = self.retrieve_convo_list(collection)

            # Retrieve Total Messages Within Past Month
            user_prompt_count = 0
            assistant_loc_count = 0
            assistant_sentence_count = 0
            for convo in convo_list:
                if self.is_document_within_past_days(convo, 30):
                    user_prompt_count += self.retrieve_user_message_count(convo)
                    convo_loc, convo_sentences = self.retrieve_assistant_data(convo)
                    assistant_loc_count += convo_loc
                    assistant_sentence_count += convo_sentences

            # Store Required Metrics Before Writing
            user_convo_details[user] = {}
            user_convo_details[user]['Conversation Count'] = collection.count_documents({})
            user_convo_details[user]['Total User Prompts'] = user_prompt_count
            user_convo_details[user]['Total Assistant Explaination LOC'] = assistant_loc_count
            user_convo_details[user]['Total Assistant Explaination Sentences'] = assistant_sentence_count

        return user_convo_details
    

    def print_user_convo_details(self, details_list):
        for username, user_details in details_list.items():
            print('Username: ' + username)
            for k, v in user_details.items():
                print('\t' + k + ": " + str(v))


    def write_user_convo_details(self, details_list, file_path):
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        with open(file_path, 'w') as f:
            json.dump(details_list, f, indent=4)
    

    def is_document_within_past_days(self, document, days):
        # Document Creation DD/MM/YY
        creation_ddmmyy = ObjectId(document['_id']).generation_time.strftime("%d/%m/%y")
        creation_ddmmyy_obj = datetime.strptime(creation_ddmmyy, "%d/%m/%y")

        # 30 Days Ago From Now
        thirty_days_ago_ddmmyy = (datetime.now() - timedelta(days=days)).strftime("%d/%m/%y")
        thirty_days_ago_ddmmyy_obj = datetime.strptime(thirty_days_ago_ddmmyy, "%d/%m/%y")

        if creation_ddmmyy_obj >= thirty_days_ago_ddmmyy_obj:
            return True
        else:
            return False
    

    def count_lines_from_text(self, text, marker='```'):
            loc = 0
            sentences = 0
            in_code_block = False
            for line in text.split('\n'):
                if marker in line:
                    in_code_block = not in_code_block
                elif in_code_block:
                    loc += 1
                elif not in_code_block:
                    sentences += 1
            return (loc, sentences)


    def retrieve_user_list(self, db):
        return db.list_collection_names()


    def retrieve_convo_list(self, collection):
        return collection.find()


    def retrieve_user_message_count(self, document):
        user_prompts = 0
        for message in document['messages']:
            if message['role'] == 'user':
                user_prompts += 1
        return user_prompts
    

    def retrieve_assistant_data(self, document):
        total_loc = 0
        total_sentences = 0
        for message in document['messages']:
            if message['role'] == 'assistant':
                loc, sentences = self.count_lines_from_text(message['content'])
                total_loc += loc
                total_sentences += sentences

        return (total_loc, total_sentences)
