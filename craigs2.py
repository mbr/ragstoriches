#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from lxml.html import document_fromstring
from ragstoriches.scraper import Scraper

scraper = Scraper(__name__)

@scraper
def index(requests, url='http://eastidaho.craigslist.org/search/act?query=+'):
    html = document_fromstring(requests.get(url).content)

    for ad_link in html.cssselect('.row a'):
        yield 'posting', ad_link.get('href')

    nextpage = html.cssselect('.nextpage a')
    if nextpage:
        yield 'index', nextpage[0].get('href')


@scraper
def posting(requests, url, push_data):
    html = document_fromstring(requests.get(url).content)

    push_data('posting', {
        'title': html.cssselect('.postingtitle')[0].text.strip(),
        'id': re.findall(r'\d+', html.cssselect('div.postinginfos p')[0].text)[0],
        'date': html.cssselect('.postinginfos date')[0].text.strip(),
        'body': html.cssselect('#postingbody')[0].text_content().strip(),
    })
