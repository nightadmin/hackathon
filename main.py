#!/bin/python3
import json, asyncio
from pymongo import *
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

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

TOKEN = "f676467e994ad120786030548f6b0c308d884e58c2fd71ba1019f5342e963e7d4765d18716ee91e61cae0"
vks = vk_api.VkApi(token=TOKEN)
vks._auth_token()
longpoll = VkBotLongPoll(vks, "209723934")
vk = vks.get_api()



def send(message,tok,peer_id,reply=None):
    return json.loads(requests.post("https://api.vk.com/method/messages.send?v=5.131&random_id=0",data={'peer_ids': [peer_id], 'reply_to': reply,'message': message,'access_token':tok}).content.decode('utf-8'))

async def start_cb(event):
    '''Стартовая команда'''
    a = vk.users.get(user_ids = [event.message["from_id"]])
    firstname = a[0]["first_name"]
    send(f"Привет, {firstname}!\nЭто бот для поиска идеального подарка. Для сбора подарка напишите \"Сбор\".", TOKEN, event.message["peer_id"])

async def start_gift_collecting_cb(event):
    uid = event.message["from_id"]
    if not find_document(sessions, {"uid": uid}):
        '''Сессий еще нет, создаем новую'''
        send(f"Итак, будем собирать новый подарок.", TOKEN, event.message["peer_id"])
        s = {
            "uid": uid,
            "step": "create",
            "step_id": 1
        }
        insert_document(sessions, s)
        send(f"Для начала, выберите пол человека.", TOKEN, event.message["peer_id"])
    else:
        send(f"Похоже, вы не закончили с предыдущим подарком. Желаете сбросить прогресс?", TOKEN, event.message["peer_id"])

async def gift_collecting_cb(event):
    uid = event.message["from_id"]
    res = find_document(sessions, {"uid": uid})
    if not res:
        '''Сессий еще нет, и она похоже не нужна.'''
        return
    text = event.message["text"]
    step = res["step_id"]
    if step == 1:
        '''Step "creating", nothing data'''
        if text.lower() not in ['мужской', 'женский', 'неважно']:
            send(f"Пол, который вы ввели, некорректный.", TOKEN, event.message["peer_id"])
            return
        genders = {
            "мужской": 1,
            "женский": 2,
            "неважно": 0
        }
        gender = genders[text.lower()]
        update_document(sessions, {"uid": uid}, {"gender": gender, "step": "gender", "step_id": 2})
        send(f"Теперь укажите бюджет - два числа в рублях через символ \"-\" без пробелов.", TOKEN, event.message["peer_id"])
    if step == 2:
        '''Step "gender", gender data saved'''
        try:
            nums = [int(x) for x in text.split("-")]
            if len(nums) != 2:
                raise ValueError
            if nums[0] < 0 or nums[1] < 0:
                raise ValueError
        except Exception:
            send(f"Числа, которые вы ввели, некорректны. Проверьте, что цены записаны через дефис без пробелов и других символов.", TOKEN, event.message["peer_id"])
            return
        update_document(sessions, {"uid": uid}, {"price": [nums[0], nums[1]], "step": "price", "step_id": 3})
        send(f"Потрясно! Теперь выберите тип подарка - личный, тематический или корпоративный.", TOKEN, event.message["peer_id"])
    if step == 3:
        '''Step "price", gender and price data saved'''
        uid = event.message["from_id"]
        text = event.message["text"]
        if text.lower() not in ['личный', 'корпоративный', 'тематический']:
            send(f"Вы неправильно указали тип подарка. Выберите что-то одно: личный (от человека человеку), корпоративный (от компании людей человеку/компании людей), тематический (что-то специфическое).", TOKEN, event.message["peer_id"])
            return
        types = {
            "личный": 0,
            "корпоративный": 2,
            "тематический": 1
        }
        gtype = types[text.lower()]
        update_document(sessions, {"uid": uid}, {"type": gtype, "step": "type", "step_id": 4})
        
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Новогодний', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        gtypes = ['Ко дню рождения', 'День защитника Отечества', '8 марта', 'День Победы', 'День знаний']
        for i in gtypes:
            keyboard.add_button(i, color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
        keyboard.add_button('Просто так.', color=VkKeyboardColor.PRIMARY)
        vk.messages.send(
            peer_id=event.message['peer_id'],
            random_id=0,
            keyboard=keyboard.get_keyboard(),
            message=f"Ух ты... ваш {text.lower()} подарок точно будет потрясающим. Чтобы правильно подобрать его, укажите тематику подарка: проще будет воспользоваться кнопками или выбрать вариант \"Просто так\"."
        )
    if step == 4:
        '''Step "type", gender, price and type data saved'''
        uid = event.message["from_id"]
        text = event.message["text"]
        if text not in ['Ко дню рождения', 'День защитника Отечества', '8 марта', 'День Победы', 'День знаний', 'Новогодний', 'Просто так.']:
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button('Новогодний', color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            gtypes = ['Ко дню рождения', 'День защитника Отечества', '8 марта', 'День Победы', 'День знаний']
            for i in gtypes:
                keyboard.add_button(i, color=VkKeyboardColor.SECONDARY)
                keyboard.add_line()
            keyboard.add_button('Просто так.', color=VkKeyboardColor.PRIMARY)
            vk.messages.send(
                peer_id=event.message['peer_id'],
                random_id=0,
                keyboard=keyboard.get_keyboard(),
                message=f"Вы неправильно указали тематику подарка. Чтобы правильно выбрать тематику, воспользуйтесь кнопками или выбрать вариант \"Просто так\"."
            )
            return
        gtems = {
            "Новогодний": 1,
            "Ко дню рождения": 2,
            "День защитника Отечества": 3,
            "8 марта": 4,
            "День Победы": 5,
            "День знаний": 6,
            "Просто так.": 7
        }


TOKEN = "f676467e994ad120786030548f6b0c308d884e58c2fd71ba1019f5342e963e7d4765d18716ee91e61cae0"
vks = vk_api.VkApi(token=TOKEN)
vks._auth_token()
longpoll = VkBotLongPoll(vks, "209723934")
vk = vks.get_api()


async def dispatch(event):
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.message['text'].lower() in ['начать', 'старт']:
            asyncio.create_task(start_cb(event))
            return
        if event.message['text'].lower() in ['сбор', 'сборка']:
            asyncio.create_task(start_gift_collecting_cb(event))
            return
        
        '''Если это не команда, то это, вероятно, текст.'''
        asyncio.create_task(gift_collecting_cb(event))

for event in longpoll.listen():
    print(event)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(dispatch(event)))