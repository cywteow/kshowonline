from requests import Session
from bs4 import BeautifulSoup
from resources.lib.database import InternalDatabase, ExternalDatabase
import re
import requests
import urlparse
import json
import string

digs = string.digits + string.ascii_letters

session = Session()

domain = 'https://www2.gogoanime.video'

def request(url, headers={}):
    response = session.get(url, headers=headers, allow_redirects=False)
    print(response)
    if response.status_code == 200 or response.status_code == 302 or response.status_code == 301:
        response.encoding = 'utf-8'
        return response

def requestpost(url, headers={}, data={}):
    response = session.post(url, headers=headers, data=data, allow_redirects=False)
    print(response)
    if response.status_code == 200 or response.status_code == 302:
        response.encoding = 'utf-8'
        return response

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
}

def player(id):
    url = "https://www.kshowonline.com/index.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
    }
    response = requestpost(url, headers=headers, data={"watch":"1", "episode_id": id})
    iframe = BeautifulSoup(response.text, 'html.parser').find('iframe')
    obj = {
        'server': iframe['data-server'],
        'src': iframe['src']
    } 
    return obj

# response = request("https://kshowonline.com/kshow/12539-[engsub]-running-man-ep.524")
# document = BeautifulSoup(response.text, 'html.parser').find('div', id="data-episode")
# for tr in document.find_all('tr'):
#     # server = tr.find('td').string
#     span = tr.find('span', class_="eps")

#     obj = player(span['id'])
#     server = obj['server']
#     src = obj['src']
#     print(server)
#     print(src)





    





