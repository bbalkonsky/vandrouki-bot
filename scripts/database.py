import configparser
import sqlite3

from scripts.sources import *

config = configparser.ConfigParser()
config.read('config.ini')

database = config['FILES']['USER_BASE']


def create_database():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users(user_id text, cities text, is_adding text)')
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS sources(source_name, source_link, selector, class, last_post, penult_post)')
    connection.commit()
    connection.close()


def read_users():
    users = []
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for user in cursor.execute('SELECT * FROM users'):
        users.append({'user_id': user[0], 'cities': user[1], 'is_adding': user[2]})
    connection.commit()
    connection.close()
    return users


def create_user(user_id):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    is_user_exist = cursor.execute("SELECT user_id FROM users WHERE user_id = :user_id", {
        'user_id': user_id}).fetchone()
    if is_user_exist == None:
        cursor.execute("INSERT INTO users VALUES (:user_id, :cities, :is_adding)",
                       {'user_id': user_id, 'cities': 'i_want_to_get_all_cities',
                        'is_adding': '0'})
    connection.commit()
    connection.close()


def edit_user(user_id, cities):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET cities = :cities WHERE user_id = :user_id', {
        'user_id': user_id, 'cities': cities})
    connection.commit()
    connection.close()


def get_user_cities(user_id):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    user_adding = cursor.execute('SELECT cities FROM users WHERE user_id = :user_id', {
        'user_id': user_id}).fetchone()[0]
    connection.commit()
    connection.close()
    return user_adding


def get_user_adding(user_id):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    user_adding = cursor.execute('SELECT is_adding FROM users WHERE user_id = :user_id', {
        'user_id': user_id}).fetchone()[0]
    connection.commit()
    connection.close()
    return user_adding


def set_user_adding(user_id, status):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET is_adding = :status WHERE user_id = :user_id', {
        'user_id': user_id, 'status': status})
    connection.commit()
    connection.close()


def init_last_posts():
    sources_sites = get_sources_sites()
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for source in sources_sites:
        is_exist = cursor.execute("SELECT * FROM sources WHERE source_name = :source_name",
                                  {'source_name': source['source_name']}).fetchone()
        if not is_exist:
            cursor.execute(
                "INSERT INTO sources VALUES (:source_name, :source_link, :selector, :class, :last_post, :penult_post)",
                {
                    'source_name': source['source_name'],
                    'source_link': source['source_link'],
                    'selector': source['selector'],
                    'class': source['class'],
                    'last_post': source['last_post'],
                    'penult_post': source['penult_post']
                }
            )
    connection.commit()
    connection.close()


def set_last_posts(source_name, last_post, penult_post):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute(
        'UPDATE sources SET last_post = :last_post, penult_post = :penult_post WHERE source_name = :source_name',
        {'last_post': last_post, 'penult_post': penult_post, 'source_name': source_name})
    connection.commit()
    connection.close()


def get_sources():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    response = cursor.execute("SELECT source_name, source_link, selector, class, last_post, penult_post FROM sources")
    result = [
        {'source_name': source[0],
         'source_link': source[1],
         'selector': source[2],
         'class': source[3],
         'last_post': source[4],
         'penult_post': source[5]
         } for source in response
    ]
    connection.close()
    return result
