#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urlparse import urljoin

from ragstoriches import Scraper

rr = Scraper('Sample scraper')

@rr.scraper
def index(requests, context, url):
    data = requests.get(url).json()
    for i in data:
        yield 'lucky_number', context, urljoin(url, '/lucky-number-%d' % i)

@rr.scraper
def lucky_number(requests, context, url):
    print requests.get(url).text
