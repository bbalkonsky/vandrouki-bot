import configparser
import time
from multiprocessing import Process

import random
import telebot
from scripts.database import *
from scripts.helpers import *

config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['ACCESS']['TOKEN']
URL = config['HOOK']['URL']
CERT = config['HOOK']['CERT']

bot = telebot.TeleBot(TOKEN, threaded=False)


def endless_parsing():
    while True:
        try:
            period = random.randint(60, 90)
            posts_for_users = get_users_updates()
            send_user_update(bot, posts_for_users)
            time.sleep(period)
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            error = template.format(type(ex).__name__, ex.args)
            print(error)


@bot.message_handler(commands=['start'])
def start(message):
    create_user(message.chat.id)
    bot.send_photo(message.chat.id, open('pchola.jpeg', 'rb'))
    bot.send_message(message.chat.id, 'ZDAROVA!')
    bot.send_message(
        message.chat.id,
        text='Пока ты не изменишь список городов, тебе будут приходить уведомления по следующим ключевым словам:\nМосква, Санкт-петербург, Екатеринбург, Турция, Европа\nКак это сделать и вся остальная информация доступна по команде /help')


@bot.message_handler(commands=['set'])
def set_adding(message):
    set_user_adding(message.chat.id, '1')
    bot.send_message(
        message.chat.id,
        'Введи города в разных вариантах написания и через запятую, например: \nСанкт-Петербург, Петербург, Питер, Москва, Таллин')


@bot.message_handler(commands=['get'])
def get_cities(message):
    user_cities = get_user_cities(message.chat.id)
    if len(user_cities) > 0:
        list_of_cities = user_cities.split(',')
        capital_cities = map(lambda x: x.strip().capitalize(), list_of_cities)
        bot.send_message(message.chat.id, text='Вы отслеживаете следующие города:\n{}'.format(
            ', '.join(capital_cities)))
    else:
        bot.send_message(message.chat.id, text='Вы ничего не отслеживаете')


@bot.message_handler(commands=['stop'])
def get_cities(message):
    edit_user(message.chat.id, '')
    bot.send_message(
        message.chat.id, text='Вам больше не будут приходить уведомления =(')


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id, text='''
Я - клевый бот, который поможет тебе получать акции с сайта vandrouki.ru только с интересующими тебя городами и странами!\n
В этом тебе помогут следующие команды:
/set - ввести список городов
/get - посмотреть, что вы отслеживаете
/stop - отписаться от рассылки и забыть про скидки''')


@bot.message_handler(commands=['status'])
def status(message):
    result = ''
    for line in read_users():
        result += '{}: {}\n'.format(line['user_id'], line['cities'])
    bot.send_message(message.chat.id, result)


@bot.message_handler()
def handle_message(message):
    if (message.text.strip() != 0 or message.content_type != 'text'):
        if get_user_adding(message.chat.id) == '1':
            edit_user(message.chat.id, preprocesd_cities(message.text))
            set_user_adding(message.chat.id, '0')
            bot.send_message(message.chat.id, text='Список городов сохранен')
        else:
            bot.send_message(message.chat.id, text='Приветики =)')
    else:
        bot.send_message(message.chat.id, text='Шо?')


def get_bot_update(update):
    bot.process_new_updates([update])


def set_hook():
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(url='https://{}/HOOK'.format(URL),
                    certificate=open(CERT, 'rb'))


def main():
    create_database()
    init_last_posts()
    client_process = Process(target=endless_parsing, args=())
    client_process.start()
