#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urlparse import urljoin
import re

from bs4 import BeautifulSoup
from ragstoriches.scraper import Scraper

rr = Scraper(__name__)

@rr.scraper
def index(requests, context,
    url='http://eastidaho.craigslist.org/search/act?query=+'):

    soup = BeautifulSoup(requests.get(url).text)

    # progress looks a bit nicer if we fetch all indexes first
    nextpage = soup.find(class_='nextpage')
    if nextpage:
        yield 'index', context, urljoin(url, nextpage.find('a').attrs['href'])

    for row in soup.find_all(class_='row'):
        yield 'posting', context, urljoin(url, row.find('a').attrs['href'])


@rr.scraper
def posting(requests, context, url):
    soup = BeautifulSoup(requests.get(url).text)
    infos = soup.find(class_='postinginfos').find_all(class_='postinginfo')

    title = soup.find(class_='postingtitle').text.strip()
    id = re.findall('\d+', infos[0].text)[0]
    date = infos[1].find('date').text.strip()
    body = soup.find(id='postingbody').text.strip()

    print title
    print '=' * len(title)
    print 'post *%s*, posted on %s' % (id, date)
    print body
    print