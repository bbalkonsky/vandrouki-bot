import time
import re

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from telebot import types

from scripts.database import *

HEADERS = {'User-Agent': 'My User Agent 1.0'}


def get_posts(source: object):
    headers = {'User-Agent': 'My User Agent 1.0'}
    response = requests.get(source['source_link'], headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        return soup.findAll(source['selector'], attrs={"class": source['class']})
    else:
        print('error', source['source_name'], response)


def find_new_posts(source_name, new_posts, last_post, penult_post):
    new_posts_links = [post.find('a')['href'] for post in new_posts]
    if len(new_posts_links):
        if last_post in new_posts_links:
            result = new_posts_links[:new_posts_links.index(last_post)]
        elif penult_post in new_posts_links:
            result = new_posts_links[:new_posts_links.index(penult_post)]
        else:
            result = []

        if len(result) == 1:
            set_last_posts(source_name, new_posts_links[0], last_post)
        elif len(new_posts_links) >= 2:
            set_last_posts(source_name, new_posts_links[0], new_posts_links[1])
        else:
            set_last_posts(source_name, new_posts_links[0], new_posts_links[0])
    else:
        result = []
    return result


def post_preprocessing(soup, source):
    title = soup.find('h1', attrs={'class': 'entry-title'}).text

    if source == 'vandrouki':
        content = soup.find('div', attrs={"class": "entry-content"})
        img_link = soup.find('div', attrs={"class": "post-thumb"}).img['src']
    elif source == 'trip4you':
        content = soup.find('div', attrs={"class": "entry-content"})
        img_link = soup.find('img', attrs={"class": "attachment-post-thumbnail"})['src']
    elif source == 'pirates':
        content = soup.find('div', attrs={"class": "entry"})
        img_link = soup.find('div', attrs={"class": "single-post-thumb"}).img['src']
    elif source == 'sandal':
        content = soup.find('div', attrs={"class": "post-content"})
        img_link = soup.find('img', attrs={"class": "wp-post-image"})['src']
    elif source == 'radar':
        content = soup.find('div', attrs={"class": "entry-inner"})
        img_link = 'https://s19623.pcdn.co/wp-content/uploads/2019/08/solo-travel.jpg'

    text = re.sub('[*().,/+0-9!?:—=]', ' ', title)
    for i in content.findAll(['p', 'li']):
        text += ' ' + re.sub('[*().,/+0-9!?:—=\s{2,}]', ' ', i.text)
    # text = re.sub('\s{2,}', ' ', text)
    text = text.lower().strip()
    text = text.split(' ')
    return {
        'title': title,
        'content': list(filter(lambda x: len(x) > 2, text)),
        'img_link': img_link
    }


def get_new_posts_info(source, new_posts_links):
    new_posts_info = []
    for post in new_posts_links:
        new_response = requests.get(post, headers={'User-Agent': 'My User Agent 1.0'})
        if new_response.status_code == 200:
            new_soup = BeautifulSoup(new_response.text, 'lxml')

            processed_post = post_preprocessing(new_soup, source)
            new_posts_info.append({
                'link': post,
                'title': processed_post['title'],
                'content': processed_post['content'],
                'img_link': processed_post['img_link']
            })
        else:
            print('error', source, new_response)
    return new_posts_info


def find_ngrams(input_list, n):
    bigrams_list = list(zip(*[input_list[i:] for i in range(n)]))
    return [' '.join(x) for x in bigrams_list]


def find_matches(text, city):
    city_length = len(city.split())
    if city_length > 1:
        text = find_ngrams(text, city_length)
    else:
        text = [word for word in text if len(word) >= len(city) - 1]
    matches = process.extract(city, text)
    top_matches = list(filter(lambda x: x[1] > 80, matches))
    matches_list = list(map(lambda x: x[0], top_matches))
    return bool(len(matches_list))


def find_user_links(cities, new_posts):
    links_to_user = []
    for post in new_posts:
        post_result = {
            'link': post['link'],
            'title': post['title'],
            'img_link': post['img_link'],
            'matches': []
        }
        for city in cities:
            matches = find_matches(post['content'], city)
            if matches:
                post_result['matches'].append(city)
        if len(post_result['matches']):
            links_to_user.append(post_result)
    return links_to_user


def create_button(link):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text='Смотреть!', url=link)])
    return keyboard


def preprocesd_cities(cities):
    commas = re.sub('[;.:@#%$^*]', ',', cities)
    no_whitespaces = re.sub('\s+', ' ', commas)
    splitted = no_whitespaces.split(',')
    stripped = map(lambda x: x.strip(), splitted)
    return ','.join(stripped).strip()


def get_all_cities(users):
    cities = ()
    for user in users:
        for city in user['cities'].split(','):
            cities += (city,)
    return cities


def check_updates(users):
    sources = get_sources()

    raw_posts = {}
    for source in sources:
        raw_posts[source['source_name']] = get_posts(source)

    new_links = {}
    last_posts_by_sources = {i['source_name']: {'last_post': i['last_post'], 'penult_post': i['penult_post']} for i in
                             sources}
    for source in raw_posts:
        new_links[source] = find_new_posts(source, raw_posts[source], last_posts_by_sources[source]['last_post'],
                                           last_posts_by_sources[source]['penult_post'])

    new_posts = []
    for source in new_links:
        time.sleep(2)
        new_posts += get_new_posts_info(source, new_links[source])

    cities = get_all_cities(users)
    post_by_cities = []
    for link in find_user_links(cities, new_posts):
        post_by_cities.append(link)

    return post_by_cities


def get_updates_by_users(users, all_links):
    full_result = []
    for user in users:
        user_result = []
        for link in all_links:
            for city in user['cities'].split(','):
                if city in link['matches']:
                    results_list = list(map(lambda res: res['link'], user_result))
                    if len(user_result) and link['link'] in results_list:
                        user_result[results_list.index(link['link'])]['matches'].append(city)
                    else:
                        user_result.append({
                            'title': link['title'],
                            'link': link['link'],
                            'img': link['img_link'],
                            'matches': [city]
                        })
        if len(user_result):
            full_result.append({
                'user_id': user['user_id'],
                'matches': user_result
            })
    return full_result


def get_users_updates():
    users = read_users()
    new_posts = check_updates(users)
    user_updates = get_updates_by_users(users, new_posts)

    posts_for_users = []
    for user in user_updates:
        for match in user['matches']:
            tag_cities = ''
            for city in match['matches']:
                city = city.replace('-', ' ').split(' ')
                city = map(lambda x: x.capitalize(), city)
                city = ''.join(city)
                tag_cities += '#{} '.format(city)
            posts_for_users.append({'user_id': user['user_id'],
                                    'tags': tag_cities,
                                    'post_title': match['title'],
                                    'post_img': match['img'],
                                    'post_url': match['link']})
    return posts_for_users


def send_user_update(bot, posts_for_users):
    for post in posts_for_users:
        bot.send_message(post['user_id'],
                         text='{}\n{}[!]({})'.format(post['tags'], post['post_title'], post['post_img']),
                         parse_mode='Markdown', reply_markup=create_button(post['post_url']))
