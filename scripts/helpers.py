import re
import time

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from telebot import types

from scripts.database import *

HEADERS = {'User-Agent': 'My User Agent 1.0'}


def get_all_posts_by_sources(sources):
    """Get all posts by list of sources"""
    try:
        raw_posts = {}
        for source in sources:
            headers = {'User-Agent': 'My User Agent 1.0'}
            response = requests.get(source['source_link'], headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                found_posts = soup.findAll(source['selector'], attrs={"class": source['class']})
                raw_posts[source['source_name']] = found_posts
            else:
                print('get_all_posts_by_sources network error,', source['source_name'], response)  # this shit into logs
        return raw_posts
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('get_all_posts_by_sources error')
        print(error)


def find_new_posts(sources, raw_posts):
    try:
        new_links = {}
        last_posts_by_sources = {i['source_name']: {'last_post': i['last_post'], 'penult_post': i['penult_post']} for i
                                 in
                                 sources}

        for source_name in raw_posts:

            new_posts_links = [post.find('a')['href'] for post in raw_posts[source_name]]
            if len(new_posts_links):
                last_post = last_posts_by_sources[source_name]['last_post']
                penult_post = last_posts_by_sources[source_name]['penult_post']

                if last_post in new_posts_links:
                    result = new_posts_links[:new_posts_links.index(last_post)]
                elif penult_post in new_posts_links:
                    result = new_posts_links[:new_posts_links.index(penult_post)]
                else:
                    result = []

                if len(result) == 1:
                    set_last_posts(source_name, new_posts_links[0], last_post)  # <=============дублепиздец
                elif len(new_posts_links) >= 2:
                    set_last_posts(source_name, new_posts_links[0], new_posts_links[1])
                else:
                    set_last_posts(source_name, new_posts_links[0], new_posts_links[0])
            else:
                result = []
            if len(result):
                new_links[source_name] = result
        return new_links
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('find_new_posts error')
        print(error)


def post_preprocessing(soup, source):
    try:
        title = soup.find('h1', attrs={'class': 'entry-title'}).text

        if source == 'vandrouki':  # <============================ оишбки обработай, додик
            content = soup.find('div', attrs={"class": "entry-content"})
            img_link = soup.find('div', attrs={"class": "post-thumb"}).img['src']
        elif source == 'trip4you':
            content = soup.find('div', attrs={"class": "entry-content"})
            img_link = soup.find('img', attrs={"class": "attachment-post-thumbnail"})['src']
        elif source == 'pirates.travel':
            content = soup.find('div', attrs={"class": "entry"})
            img_link = soup.find('div', attrs={"class": "single-post-thumb"}).img['src']
        elif source == 'travelsandal':
            content = soup.find('div', attrs={"class": "post-content"})
            img_link = soup.find('img', attrs={"class": "wp-post-image"})['src']
        elif source == 'travelradar':
            content = soup.find('div', attrs={"class": "entry-inner"})
            img = soup.find('meta', attrs={"property": "og:image"})
            if img:
                img_link = img['content']
            else:
                img_link = 'https://kapets.net/wp-content/uploads/2019/04/travel-editor-favorite-products.jpg'

        text = re.sub('[*().,/+0-9!?:—=]', ' ', title)
        if source == 'travelradar':  # <================================== pizdec konechno
            for i in content.findChildren(['p', 'li', 'h4'], recursive=False):
                text += ' ' + re.sub('[*().,/+0-9!?:—=\s{2,}]', ' ', i.text)
        else:
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
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('post_preprocessing error')
        print(error)


def get_new_posts_info(new_links):
    try:
        new_posts_info = []

        for source_name in new_links:
            for post in new_links[source_name]:
                time.sleep(5)
                new_response = requests.get(post, headers={'User-Agent': 'My User Agent 1.0'})
                if new_response.status_code == 200:
                    new_soup = BeautifulSoup(new_response.text, 'lxml')

                    processed_post = post_preprocessing(new_soup, source_name)
                    new_posts_info.append({
                        'link': post,
                        'title': processed_post['title'],
                        'content': processed_post['content'],
                        'img_link': processed_post['img_link'],
                        'source_name': source_name
                    })
                else:
                    print('get_new_posts_info network error', source_name, new_response)
        return new_posts_info
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('get_new_posts_info error')
        print(error)


def find_ngrams(input_list, n):
    try:
        bigrams_list = list(zip(*[input_list[i:] for i in range(n)]))
        return [' '.join(x) for x in bigrams_list]
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('find_ngrams error')
        print(error)


def find_matches(text, city):
    try:
        city_length = len(city.split())
        if city_length > 1:
            text = find_ngrams(text, city_length)
        else:
            text = [word for word in text if len(word) >= len(city) - 1]
        matches = process.extract(city, text)
        top_matches = list(filter(lambda x: x[1] > 80, matches))
        matches_list = list(map(lambda x: x[0], top_matches))
        return bool(len(matches_list))
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('find_matches error')
        print(error)


def find_posts_by_every_city(cities, new_posts):
    try:
        """Get list of posts with list of post cities"""
        posts_by_cities = []
        for post in new_posts:
            post_result = {
                'link': post['link'],
                'title': post['title'],
                'img_link': post['img_link'],
                'source_name': post['source_name'],
                'matches': ['i_want_to_get_all_cities']
            }
            for city in cities:
                matches = find_matches(post['content'], city)
                if matches:
                    post_result['matches'].append(city)
            posts_by_cities.append(post_result)
        return posts_by_cities
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('find_posts_by_every_city error')
        print(error)


def create_button(post_url, source_name):
    try:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*[types.InlineKeyboardButton(text=source_name.capitalize(), url=post_url)])
        return keyboard
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('create_button error')
        print(error)


def preprocesd_cities(cities):
    try:
        commas = re.sub('[;.:@#%$^*]', ',', cities)
        no_whitespaces = re.sub('\s+', ' ', commas)
        splitted = no_whitespaces.split(',')
        stripped = map(lambda x: x.strip(), splitted)
        return ','.join(stripped).strip().lower()
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('preprocesd_cities error')
        print(error)


def get_all_cities(users):
    try:
        cities = set()
        for user in users:
            for city in user['cities'].split(','):
                cities.add(city.strip().lower())
        return cities
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('get_all_cities error')
        print(error)


def city_to_hashtag(city):
    try:
        if city == 'i_want_to_get_all_cities':
            return ''
        city = city.strip().replace('-', ' ').split(' ')
        city = map(lambda x: x.capitalize(), city)
        city = ''.join(city)
        return '#' + city
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('city_to_hashtag error')
        print(error)


def get_posts_for_users(users, all_posts):
    try:
        """Get a list of posts prepared for sending to users"""
        full_result = []
        for user in users:
            user_result = []
            for post in all_posts:
                for city in user['cities'].split(','):
                    if city.strip().lower() in post['matches']:
                        results_list = list(map(lambda res: res['post_url'], user_result))
                        if not (len(user_result) and post['link'] in results_list):
                            post_tags = ''
                            for tag in post['matches']:
                                if tag != 'i_want_to_get_all_cities':
                                    post_tags += city_to_hashtag(tag) + ' '

                            user_result.append({
                                'user_id': user['user_id'],
                                'post_title': post['title'],
                                'post_url': post['link'],
                                'post_img': post['img_link'],
                                'tags': post_tags.strip(),
                                'source_name': post['source_name']
                            })
                        break
            full_result += user_result
        return full_result
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('get_posts_for_users error')
        print(error)


def send_users_updates(bot, posts_for_users):
    try:
        for post in posts_for_users:
            post_title = post['post_title'].replace('*', '\U00002B50').replace('_', '-')  # replace because markdown
            bot.send_message(post['user_id'], text='{}\n{}[!]({})'.format(post['tags'], post_title, post['post_img']),
                             parse_mode='Markdown', reply_markup=create_button(post['post_url'], post['source_name']))
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        error = template.format(type(ex).__name__, ex.args)
        print('send_users_updates error')
        print(error)
