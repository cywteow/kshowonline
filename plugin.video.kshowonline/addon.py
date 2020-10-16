# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from requests import Session
from rerouting import Rerouting
from resources.lib.database import InternalDatabase, ExternalDatabase
from xbmc import Keyboard
from xbmcgui import Dialog, ListItem

import json
import urlparse
import requests
import os
import re
import xbmc
import xbmcplugin
import resolveurl


domain = 'https://kshowonline.com'
plugin = Rerouting()
session = Session()
attrs = vars(plugin)
print(', '.join("%s: %s" % item for item in attrs.items()))


@plugin.route('/')
def index():
    items = [
        (plugin.url_for('/recently-viewed'), ListItem("Recently viewed"), True),
        (plugin.url_for('/list/new/1/'), ListItem("Latest Shows"), True),
        (plugin.url_for('/2/1/'), ListItem("Top shows today"), True),
        (plugin.url_for('/show-list'), ListItem("Kshow List"), True)
    ]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(r'/list/new/(?P<pageNum>[0-9]+)/')
def latestShows(pageNum):
    response = request(domain+plugin.path)
    items = parsePage(response.text)
    
    if pageNum is None:
        pageNum = 1
    else:
        pageNum = int(pageNum)

    item = ListItem("Next >>")
    items.append((plugin.url_for("/list/new/"+ str(pageNum + 1)+"/"), item, True))
    if pageNum != 1:
        item = ListItem("Back to main page")
        items.append((plugin.url_for("/"), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(r'/2/(?P<pageNum>[0-9]+)/')
def topShows(pageNum):
    params = {
        'showfilm': "1",
        'num': "2",
        'page': pageNum,
        'number': "12",
        'apr': '3',
        'cat_id': '1',
        'sort': '1'

    }
    response = requestpost(domain+"/index.php", data=params)
    items = parsePage(response.text)
        
    
    if pageNum is None:
        pageNum = 1
    else:
        pageNum = int(pageNum)

    item = ListItem("Next >>")
    items.append((plugin.url_for("/2/"+ str(pageNum + 1)+"/"), item, True))
    if pageNum != 1:
        item = ListItem("Back to main page")
        items.append((plugin.url_for("/"), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)

def parsePage(text):
    items = []
    document = BeautifulSoup(text, 'html.parser').find('div', class_="content-list z-depth-1")
    for a in document.find_all('a'):
        if a.has_attr('title'):
            path = urlparse.urlparse(a['href']).path
            title = a['title']
            item = ListItem(title)
            imgTag = a.find('img')
            item.setInfo('video', {})
            if imgTag is not None:
                img = imgTag['src']
                item.setArt({'poster': img})
                item.setProperty('IsPlayable', 'true')
                items.append((plugin.url_for(path), item, False))
            else:
                items.append((plugin.url_for(path), item, True))
    
    return items

@plugin.route(r'/kshow/(.+)')
def playKshow():
    response = request(domain+plugin.pathqs)
    document = BeautifulSoup(response.text, 'html.parser').find('div', id="data-episode")
    sources = []
    for tr in document.find_all('tr'):
        span = tr.find('span', class_="eps")

        obj = player(span['id'])
        server = obj['server']
        src = obj['src']
        if "playhydrax" not in src:
            source = ListItem(server)
            source.setProperty("data-video", src)
            sources.append(source)

    position = Dialog().select("Choose server", sources)
    
    if position != -1:
        xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=resolveurl.resolve(sources[position].getProperty("data-video"))))

@plugin.route('/show-list')
def show_list():
    response = request(domain+plugin.path)
    items = parsePage(response.text)

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(r'/category/(?P<category>([^/]+)/([^/]+))(/(?P<pageNum>[0-9]+)/)?')
def category(category, pageNum):
    response = request(domain+plugin.pathqs)
    items = parsePage(response.text)
    h5 = BeautifulSoup(response.text, 'html.parser').find('div', class_="content-list z-depth-1").find('h5')
    title = h5.contents[0].strip()[10:]
    ExternalDatabase.connect()
    ExternalDatabase.add(("/category/"+category, title))
    ExternalDatabase.close()

    if pageNum is None:
        pageNum = 1
    else:
        pageNum = int(pageNum)

    item = ListItem("Next >>")
    items.append((plugin.url_for("/category/"+category+"/"+ str(pageNum + 1)+"/"), item, True))
    if pageNum != 1:
        item = ListItem("Back to main page")
        items.append((plugin.url_for("/"), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)



@plugin.route(r'/recently-viewed(\?delete=(?P<delete>.+))?')
def recently_viewed(delete=None):
    ExternalDatabase.connect()

    if delete is not None:
        ExternalDatabase.remove(delete)
        xbmc.executebuiltin('Container.Refresh')
    else:
        items = []

        for row in ExternalDatabase.fetchall():
            item = ListItem(row['title'])
            item.addContextMenuItems([
                ("Remove", 'RunPlugin(plugin://plugin.video.kshowonline/recently-viewed?delete=' + row['path'] + ')'),
                ("Remove all", 'RunPlugin(plugin://plugin.video.kshowonline/recently-viewed?delete=%)')
            ])
            item.setInfo('video', {})
            items.append((plugin.url_for(row['path']), item, True))

        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    ExternalDatabase.close()

def request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",}):
    response = session.get(url, headers=headers, allow_redirects=False)
    if response.status_code == 200 or response.status_code == 302 or response.status_code == 301:
        response.encoding = 'utf-8'
        return response

def requestpost(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",}, data={}):
    response = session.post(url, headers=headers, data=data, allow_redirects=False)
    if response.status_code == 200 or response.status_code == 302:
        response.encoding = 'utf-8'
        return response

def player(id):
    url = domain+"/index.php"
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

if __name__ == '__main__':
    plugin.run()
