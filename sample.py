#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urlparse import urljoin

from ragstoriches import Scraper

rr = Scraper('Sample scraper')

@rr.scraper
def index(requests, url, context):
    data = requests.get(url).json()
    for i in data:
        yield 'lucky_number', urljoin(url, '/lucky-number-%d' % i), context

@rr.scraper
def lucky_number(requests, url, context):
    print requests.get(url).text
