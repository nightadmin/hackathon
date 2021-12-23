#!/bin/python3
import json, asyncio
from pymongo import *
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests

"""
CRUD OPERATIONS with MongoDB
"""

# Create the client
client = MongoClient('localhost', 3001)

# Connect to our database
db = client['fg']

# Fetch our series collection
users = db['users']

sessions = db['sessions']

def insert_document(collection, data):
    """ Function to insert a document into a collection and
    return the document's id.
    """
    return collection.insert_one(data).inserted_id

def find_document(collection, elements, multiple=False):
    """ Function to retrieve single or multiple documents from a provided
    Collection using a dictionary containing a document's elements.
    """
    if multiple:
        results = collection.find(elements)
        return [r for r in results]
    else:
        return collection.find_one(elements)

def update_document(collection, query_elements, new_values):
    """ Function to update a single document in a collection.
    """
    collection.update_one(query_elements, {'$set': new_values})

def delete_document(collection, query):
    """ Function to delete a single document from a collection.
    """
    collection.delete_one(query)


def send(message,tok,peer_id,reply=None):
    return json.loads(requests.post("https://api.vk.com/method/messages.send?v=5.131&random_id=0",data={'peer_ids': [peer_id], 'reply_to': reply,'message': message,'access_token':tok}).content.decode('utf-8'))

async def start_cb(event):
    '''Стартовая команда'''
    a = vk.users.get(user_ids = [event.message["from_id"]])
    firstname = a[0]["first_name"]
    send(f"Привет, {firstname}!\nЭто бот для поиска идеального подарка. Для сбора подарка напишите \"Сбор\".", TOKEN, event.message["peer_id"])
    


TOKEN = "f676467e994ad120786030548f6b0c308d884e58c2fd71ba1019f5342e963e7d4765d18716ee91e61cae0"
vks = vk_api.VkApi(token=TOKEN)
vks._auth_token()
longpoll = VkBotLongPoll(vks, "209723934")
vk = vks.get_api()


async def dispatch(event):
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.message['text'].lower() in ['начать', 'старт']:
            asyncio.create_task(start_cb(event))
            

for event in longpoll.listen():
    print(event)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(dispatch(event)))