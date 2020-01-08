import time
from multiprocessing import Process

import telebot

from scripts.database import *
from scripts.helpers import *

config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['ACCESS']['TOKEN']
URL = config['HOOK']['URL']
CERT = config['HOOK']['CERT']

bot = telebot.TeleBot(TOKEN, threaded=False)


def check_updates():
    all_posts = get_posts()
    new_posts_links = find_new_posts(all_posts, get_last_link())
    if len(new_posts_links) == 0:
        return []
    update_last_link(new_posts_links[0])
    new_posts = get_new_posts_info(new_posts_links)
    return new_posts


def get_users_updates():
    while True:
        new_posts = check_updates()
        users = read_users()
        for user in users:
            raw_cities = user['cities']
            if len(raw_cities) != 0:
                cities = raw_cities.split(',')
                links = find_user_links(cities, new_posts)
                for link in links:
                    bot.send_message(user['user_id'], text=link['matches'])
                    bot.send_message(user['user_id'], text=link['link'])
        time.sleep(60)


@bot.message_handler(commands=['start'])
def start(message):
    create_user(message.chat.id)
    bot.send_message(message.chat.id, text='welcome!')


@bot.message_handler(commands=['set'])
def set_adding(message):
    set_user_adding(message.chat.id, '1')
    bot.send_message(message.chat.id, 'Напиши список городов через запятую:')


@bot.message_handler(commands=['status'])
def status(message):
    for line in read_users():
        bot.send_message(message.chat.id, str(line))


@bot.message_handler()
def handle_message(message):
    if get_user_adding(message.chat.id) == '1':
        edit_user(message.chat.id, message.text)
        set_user_adding(message.chat.id, '0')
        bot.send_message(message.chat.id, text='Список городов сохранен')
    else:
        bot.send_message(message.chat.id, text='Приветики =)')


def get_bot_update(update):
    bot.process_new_updates([update])


def set_hook():
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(url='https://{}/HOOK'.format(URL),
                    certificate=open(CERT, 'rb'))


def main():
    create_database()
    client_process = Process(target=get_users_updates, args=())
    client_process.start()
