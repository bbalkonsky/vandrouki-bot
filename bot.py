import random
from multiprocessing import Process

import telebot

from scripts.helpers import *

config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['ACCESS']['TOKEN']
URL = config['HOOK']['URL']
CERT = config['HOOK']['CERT']

bot = telebot.TeleBot(TOKEN)


def endless_parsing():
    while True:
        try:
            period = random.randint(60, 120)
            sources = get_sources()
            raw_posts = get_all_posts_by_sources(sources)
            new_links = find_new_posts(sources, raw_posts)
            if len(new_links):
                new_posts = get_new_posts_info(new_links)
                users = read_users()
                all_cities = get_all_cities(users)
                post_by_cities = find_posts_by_every_city(all_cities, new_posts)
                posts_for_users = get_posts_for_users(users, post_by_cities)
                send_users_updates(bot, posts_for_users)
            time.sleep(period)
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            error = template.format(type(ex).__name__, ex.args)
            print('endless_parsing error')
            print(error)


@bot.channel_post_handler(commands=['start'])
@bot.message_handler(commands=['start'])
def start(message):
    create_user(message.chat.id)
    bot.send_photo(message.chat.id, open('pchola.jpeg', 'rb'))
    bot.send_message(message.chat.id, 'ZDAROVA!')
    bot.send_message(
        message.chat.id,
        text='Отныне ты подписан на самые выгодные предложения для путешествий! Поздравляю! \nОстались вопросы? - /help')


@bot.channel_post_handler(commands=['set'])
@bot.message_handler(commands=['set'])
def set_adding(message):
    set_user_adding(message.chat.id, '1')
    bot.send_message(
        message.chat.id,
        'Введи через запятую ключевые слова для отслеживания, например: \nСанкт-Петербург, Петербург, Питер, Москва, Франция')


@bot.channel_post_handler(commands=['get'])
@bot.message_handler(commands=['get'])
def get_cities(message):
    user_cities = get_user_cities(message.chat.id)
    if len(user_cities) > 0:
        if user_cities == 'i_want_to_get_all_cities':
            bot.send_message(message.chat.id, text='Вы подписаны на все обновления')
        else:
            list_of_cities = user_cities.split(',')
            capital_cities = map(lambda x: x.strip().capitalize(), list_of_cities)
            bot.send_message(message.chat.id, text='Вы отслеживаете следующие города:\n{}'.format(
                ', '.join(capital_cities)))
    else:
        bot.send_message(message.chat.id, text='Вы ничего не отслеживаете')


@bot.channel_post_handler(commands=['stop'])
@bot.message_handler(commands=['stop'])
def get_cities(message):
    edit_user(message.chat.id, '')
    bot.send_message(
        message.chat.id, text='Вам больше не будут приходить уведомления =(')


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id, text='''
Я - клевый бот, который поможет тебе получать самые выгодные акции для путешествий только с интересующими тебя городами и странами!\n
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


@bot.channel_post_handler()
@bot.message_handler()
def handle_message(message):
    if (message.text.strip() != 0 or message.content_type != 'text'):
        if get_user_adding(message.chat.id) == '1':
            if message.text == 'все':
                edit_user(message.chat.id, 'i_want_to_get_all_cities')
            else:
                edit_user(message.chat.id, preprocesd_cities(message.text))
            set_user_adding(message.chat.id, '0')
            bot.send_message(message.chat.id, text='Список городов сохранен')
        else:
            bot.send_message(message.chat.id, text='Приветики =)')
    else:
        bot.send_message(message.chat.id, text='Шо?')
    # bot.send_message(message.chat.id, text='Приветики =)')


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
