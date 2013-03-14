#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ragstoriches',
    version='0.3.1dev',
    description='Develop highly-concurrent web scrapers, easily.',
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/ragstoriches',
    license='MIT',
    install_requires=['gevent', 'logbook', 'requests', 'requests_cache',
                      'stuf', 'colorama', 'python-dateutil'],
    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': [
            'ragstoriches = ragstoriches.apps:run_scraper',
        ],
    }
)
