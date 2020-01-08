import re

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process

HEADERS = {'User-Agent': 'My User Agent 1.0'}


def get_posts():
    url = 'http://vandrouki.ru'
    response = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(response.text, 'lxml')
    return soup.findAll('div', attrs={"class": "post"})


def find_new_posts(new_posts, last_post):
    new_posts_links = []
    for post in new_posts:
        post_link = post.find('a')['href']
        if post_link == last_post:
            break
        new_posts_links.append(post_link)
    return new_posts_links


def text_preprocessing(soup):
    title = soup.find('h1', attrs={'class': 'entry-title'}).text
    content = soup.find('div', attrs={"class": "entry-content"})

    text = re.sub('[().,/+0-9!?:—=]', ' ', title)
    for i in content.findAll(['p', 'li']):
        text += ' ' + re.sub('[().,/+0-9!?:—=]', ' ', i.text)
    text = re.sub('\s{2,}', ' ', text)
    text = text.lower().strip()
    text = text.split(' ')
    return list(filter(lambda x: len(x) > 2, text))


def get_new_posts_info(new_posts_links):
    new_posts_info = []
    for post in new_posts_links:
        new_response = requests.get(
            post, headers={'User-Agent': 'My User Agent 1.0'})
        new_soup = BeautifulSoup(new_response.text, 'lxml')

        new_posts_info.append({
            'link': post,
            'content': text_preprocessing(new_soup)
        })
    return new_posts_info


def find_matches(text, city):
    matches = process.extract(city, text)
    top_matches = list(filter(lambda x: x[1] > 80, matches))
    matches_list = list(map(lambda x: x[0], top_matches))
    return ', '.join(set(matches_list))


def find_user_links(cities, new_posts):
    links_to_user = []
    for post in new_posts:
        for city in cities:
            matches = find_matches(post['content'], city)
            if len(matches):
                links_to_user.append({
                    'link': post['link'],
                    'matches': matches
                })
                break  # find one city match - it's enough
    return links_to_user
