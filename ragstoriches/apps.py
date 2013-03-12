#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import imp
import importlib
import os
import sys

import logbook
import requests_cache

def module_type(path):
    if path.endswith('.py') and os.path.exists(path) and os.path.isfile(path):
        name = os.path.basename(path)[:-3]
        return imp.load_source('rr_%s' % name, path)
    return importlib.import_module(path)


def run_scraper():
    import gevent.monkey
    gevent.monkey.patch_all()

    """Runs a specified scraper module."""
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='Target to run.', type=module_type)
    parser.add_argument('url', help='The url to start scraping at', nargs='?')
    parser.add_argument('-c', '--cache',
                        help='Use a cache with this name to avoid '
                             'redownloading pages.')
    parser.add_argument('-d', '--debug', action='store_const',
                        const=logbook.DEBUG, dest='loglevel',
                        help='Show debugging output (useful when writing '\
                             'scrapers.')
    parser.add_argument('-e', '--encoding', default='utf8',
                        help='When stdout is redirected, change output '\
                             'encoding to this (default: utf-8). Set to '\
                             'empty string to disable.')
    parser.add_argument('-r', '--requests', default=10, type=int,
                        help='Maximum number of requests active at the same '\
                             'time.')
    parser.add_argument('-s', '--scraper', default='index',
                        help='Name of the scraper to start with.')
    parser.add_argument('-q', '--quiet', action='store_const',
                        const=logbook.WARNING, dest='loglevel',
                        help='Only output errors.')
    parser.set_defaults(targettype='autodetect', loglevel=logbook.INFO)
    args = parser.parse_args()

    logbook.handlers.NullHandler().push_application()
    logbook.handlers.StderrHandler(level=args.loglevel).push_application()

    targettype = args.targettype

    # setup stdout
    if args.encoding and not sys.stdout.isatty():
        reload(sys)
        sys.setdefaultencoding(args.encoding)

    session = None
    if args.cache:
        session = requests_cache.CachedSession(args.cache)

    scraper = args.target.scraper
    scraper.scrape(url=args.url,
                   scraper_name=args.scraper,
                   concurrency=args.requests,
                   session=session)
