# general imports
import requests
from bs4 import BeautifulSoup
import sys
from urllib import parse
import json

# kodi-related imports
import xbmcgui
import xbmcplugin

SRC_URL = "https://osgatos.net/"
addon_base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
addon_args = sys.argv[2]

def buildUrl(q):
    return f"{addon_base_url}?{parse.urlencode(q)}"

def findCategories():
    html = requests.get(SRC_URL).text
    soup = BeautifulSoup(html, "html.parser")
    a_list = soup.select("section > a")
    categories = [
        {
            'title': x.get("href"), 
            'image': parse.unquote(parse.parse_qs(parse.urlparse((x.find("img")).get("src")).query)["url"][0]) 
        } 
        for x in a_list
    ] #image is inside a NextJs request
    return categories

def findEpisodes(c_url):
    html = requests.get(c_url).text
    soup = BeautifulSoup(html, "html.parser")
    a_list = soup.select("div > a[href^='/watch/']") #href needs arg '/watch/'
    episodes = [
        {
            'title': e.select("span")[0].text.strip(),
            'link': findEpisodeLink(SRC_URL + e.get("href")),
            'image': parse.unquote(parse.parse_qs(parse.urlparse((e.find("img")).get("src")).query)["url"][0]),
            'duration': e.select("span")[1].text.strip()
        }
        for e in a_list
    ]
    return episodes

def findEpisodeLink(e_url):
    html = requests.get(e_url).text
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", type="application/ld+json")

    if script_tag:
        data = json.loads(script_tag.string)
        embed_url = data.get("embedUrl")
        return embed_url.split("/")[-1]
    else: 
        return None

def listCategories():
    categories = findCategories()

    for c in categories:
        c_title = c['title']
        c_image = c['image']
        c_name = ((c_title.split("/")[-1]).replace("-"," ")).title()
        c_url = SRC_URL + c_title
        print(c_image)

        li = xbmcgui.ListItem(label=c_name)
        li.setArt({'poster': c_image})

        kodi_url = buildUrl({'action': 'listEpisodes', 'url': c_url})
        xbmcplugin.addDirectoryItem(handle = addon_handle, url = kodi_url, listitem = li, isFolder = True)
    
    xbmcplugin.endOfDirectory(addon_handle)
    pass

def listEpisodes(c_url):
    episodes = findEpisodes(c_url)

    for ep in episodes:
        li = xbmcgui.ListItem(label=f"{ep['title']} | [{ep['duration']}]")
        li.setArt({'poster': ep['image']})
        li.setProperty('IsPlayable', 'true')

        kodi_url = buildUrl({'action': 'playEpisode', 'url': ep['link']})
        xbmcplugin.addDirectoryItem(handle = addon_handle, url = kodi_url, listitem = li, isFolder = False)
    
    xbmcplugin.endOfDirectory(addon_handle)
    pass

def playEpisode(ep_id):
    yt_url = f"plugin://plugin.video.youtube/play/?video_id={ep_id}"
    li = xbmcgui.ListItem(path=yt_url)
    xbmcplugin.setResolvedUrl(handle = addon_handle, succeeded = True, listitem = li)
    pass

def state():
    args = dict(parse.parse_qsl(addon_args.lstrip('?')))
    action = args.get('action')
    action_url = args.get('url')

    if action == 'listEpisodes':
        listEpisodes(action_url)
    elif action == 'playEpisode':
        playEpisode(action_url)
    else:
        listCategories()
    pass

if __name__ == '__main__':
    state()
