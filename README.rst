from ragstoriches
=================

``ragstoriches`` is a combined library/framework to ease writing web scrapers.
A simple example to tell the story::

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

      for row in soup.find_all(class_='row'):
          yield 'posting', context, urljoin(url, row.find('a').attrs['href'])

      nextpage = soup.find(class_='nextpage')
      if nextpage:
          yield 'index', context, urljoin(url, nextpage.find('a').attrs['href'])


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

Install the library and `BeatifulSoup 4
<https://pypi.python.org/pypi/beautifulsoup4>`_ using ``pip install
ragstoriches beautifulsoup4``, then save the above as ``craigs.py``,
finally run with ``ragstoriches craigs.py``.

You will get a bunch of jumbled input, so next step is redirecting ``stdout``
to a file::

   ragstoriches craigs.py > output.md

Try giving different urls for this scraper on the command-line:

   ragstoriches craigs.py http://newyork.craigslist.org/mnh/acc/ > output.md # hustle
   ragstoriches craigs.py http://orangecounty.craigslist.org/wet/ > output.md # writing OC
   ragstoriches craigs.py http://seattle.craigslist.org/w4m/ > output.md  # sleepless in seattle

There are a lot of commandline-options available, see ``ragstoriches --help``
for a list.
