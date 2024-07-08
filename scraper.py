import os
import time
import json
import telebot
import datetime
import requests
from telebot import types
from telebot import apihelper
from bs4 import BeautifulSoup

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

BOT_API_TOKEN = config['BOT_API_TOKEN']
url = config['url']
title_class = config['title_class']
link_class = config['link_class']

bot = telebot.TeleBot(BOT_API_TOKEN)
apihelper.DEFAULT_RETRY_TIMEOUT = 30

SUBSCRIBERS_FILE = 'subscribers.txt'

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as file:
            return set(line.strip() for line in file if line.strip().isdigit())
    return set()

def save_subscriber(user_id):
    with open(SUBSCRIBERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")
    print(f"User {user_id} has been subscribed.")

def remove_subscriber(user_id):
    user_id = str(user_id)  # Преобразование user_id в строку для корректного сравнения
    subscribers = load_subscribers()
    
    if user_id in subscribers:
        subscribers.remove(user_id)
        with open(SUBSCRIBERS_FILE, 'w') as file:
            for subscriber in subscribers:
                file.write(f"{subscriber}\n")
        print(f"User {user_id} has been unsubscribed.")
    else:
        print(f"User {user_id} is not in the subscribers list.")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Подписаться')
    markup.add(btn1)
    bot.send_message(message.from_user.id, '👋 Привет! Я твой бот-помошник!', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == 'Подписаться':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Отписаться')
        markup.add(btn1)
        save_subscriber(message.from_user.id)
        bot.send_message(message.from_user.id, 'Вы подписаны на обновления!', reply_markup=markup)
    elif message.text == 'Отписаться':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Подписаться')
        markup.add(btn1)
        remove_subscriber(message.from_user.id)
        bot.send_message(message.from_user.id, 'Вы отписаны от обновлений!', reply_markup=markup)

def notify_subscribers(new_link):
    subscribers = load_subscribers()
    for subscriber in subscribers:
        if subscriber:  # Проверка, чтобы убедиться, что subscriber не пустой
            try:
                bot.send_message(subscriber, 'Новая новость:')
                bot.send_message(subscriber, new_link)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Failed to send message to {subscriber}: {e}")

def check_for_updates():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    last_title = soup.find('span', class_=title_class).text.strip()
    
    while True:
        time.sleep(60 * 5)
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        new_title = soup.find('span', class_=title_class).text.strip()
        if new_title != last_title:
            last_title = new_title
            new_link = url + soup.find('a', class_=link_class).get('href')
            notify_subscribers(new_link)

def polling_with_retries():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            print("ReadTimeout error occurred. Retrying in 15 seconds...")
            time.sleep(15)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 15 seconds...")
            time.sleep(15)

if __name__ == '__main__':
    from threading import Thread
    update_thread = Thread(target=check_for_updates)
    update_thread.start()
    polling_with_retries()