import configparser
import sqlite3

config = configparser.ConfigParser()
config.read('config.ini')

database = config['FILES']['USER_BASE']


def create_database():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users(user_id text, cities text, is_adding text)')
    cursor.execute('CREATE TABLE IF NOT EXISTS link(last_link text)')
    if not cursor.execute("SELECT count(*) FROM link").fetchone()[0]:
        cursor.execute("INSERT INTO link VALUES ('https://vandrouki.ru/')")
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
    return (users)


def create_user(user_id):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    is_user_exist = cursor.execute("SELECT user_id FROM users WHERE user_id = :user_id", {
        'user_id': user_id}).fetchone()
    if is_user_exist == None:
        cursor.execute("INSERT INTO users VALUES (:user_id, :cities, :is_adding)",
                       {'user_id': user_id, 'cities': '', 'is_adding': '0'})
    connection.commit()
    connection.close()


def edit_user(user_id, cities):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET cities = :cities WHERE user_id = :user_id', {
        'user_id': user_id, 'cities': cities})
    connection.commit()
    connection.close()


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


# def get_user_cities(user_id):
#     connection = sqlite3.connect(database)
#     cursor = connection.cursor()
#     user_adding = cursor.execute('SELECT cities FROM users WHERE user_id = :user_id', {
#                    'user_id': user_id}).fetchone()[0]
#     connection.commit()
#     connection.close()
#     return (user_adding)


def get_last_link():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    last_link = cursor.execute('SELECT last_link FROM link').fetchone()[0]
    connection.commit()
    connection.close()
    return last_link


def update_last_link(last_link):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('UPDATE link SET last_link = :last_link', {'last_link': last_link})
    connection.commit()
    connection.close()
