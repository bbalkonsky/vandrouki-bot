import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

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


def get_new_posts_info(new_posts_links):
    new_posts_info = []
    for post in new_posts_links:
        new_response = requests.get(post, headers=HEADERS)
        new_soup = BeautifulSoup(new_response.text, 'lxml')
        post_title = new_soup.find('h1', attrs={'class': 'entry-title'}).text
        post_content = new_soup.find('div', attrs={"class": "entry-content"}).text

        new_posts_info.append({
            'link': post,
            'content': post_title + ' ' + post_content.replace('\n', ' ')
        })
    return new_posts_info


def find_user_links(cities, new_posts):
    links_to_user = []
    for post in new_posts:
        for city in cities:
            # if fuzz.partial_ratio(re.search(r'([А-Яа-я\-]+)', post['content'].lower()).group(1), city.lower()) > 80:
            # if process.extractOne("санкт-петербург", re.findall(r'([А-Яа-я\-]+)', post['content'].lower()))
            if fuzz.token_set_ratio(post['content'].lower(), city.strip().lower()) > 80:
                links_to_user.append(post['link'])
                break
    return links_to_user


