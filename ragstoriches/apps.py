#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import imp
import importlib
import os


def run_scraper():
    """Runs a specified scraper module."""
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='Target to run.')
    parser.add_argument('-m', '--module', help='Target is a module.',
                        action='store_const', const='module',
                        dest='targettype')
    parser.add_argument('-f', '--file', help='Target is a file (the default).',
                        dest='targettype', action='store_const', const='file')
    parser.set_defaults(targettype='autodetect')
    args = parser.parse_args()

    targettype = args.targettype

    if targettype == 'autodetect':
        targettype = 'file' if os.path.exists(args.target) else 'module'

    if targettype == 'file':
        mod = imp.load_source('__ragstoriches_main', args.target)
    elif targettype == 'module':
        mod = importlib.import_module(args.target)

    scraper = mod.rr

    scraper.scrape('http://localhost:5000')
