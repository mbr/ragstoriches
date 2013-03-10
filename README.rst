from ragstoriches
=================

``ragstoriches`` is a combined library/framework to ease writing web scrapers
using gevent and requests.

A simple example to tell the story:

.. code-block:: python

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

Install the library and `BeautifulSoup 4
<https://pypi.python.org/pypi/beautifulsoup4>`_ using ``pip install
ragstoriches beautifulsoup4``, then save the above as ``craigs.py``,
finally run with ``ragstoriches craigs.py``.

You will get a bunch of jumbled input, so next step is redirecting ``stdout``
to a file::

   ragstoriches craigs.py > output.md

Try giving different urls for this scraper on the command-line:

.. code-block:: sh

   ragstoriches craigs.py http://newyork.craigslist.org/mnh/acc/  > output.md  # hustle
   ragstoriches craigs.py http://orangecounty.craigslist.org/wet/ > output.md  # writing OC
   ragstoriches craigs.py http://seattle.craigslist.org/w4m/      > output.md  # sleepless in seattle

There are a lot of commandline-options available, see ``ragstoriches --help``
for a list.


Writing scrapers
----------------

A scraper module consists of some initialization code and a number of
subscrapers. Scraping starts by calling the a scraper named ``index`` on the
scraper ``rr`` in the moduel (see the example above).

The ``requests`` argument should be treated like the `requests
<http://python-requests.org>`_ module (it actually is an instance of requests
Pool). As long as you use it for fetching webpages, you never have to worry
about blocking or exceeding concurrency limits.

The ``context`` variable is arbitrary, but by convention a dictionary. It's a
way of passing state from one scraper to another or sharing it. It is only
passed on by ``ragstoriches`` and never touched otherwise.

The ``url`` is the url to scrape and parse.

Return values of scrapers are ignored. However, if a scraper is a generater
(i.e. contains a yield statement), any value it yields must be a 3-tuple
consisting of the name of a scraper, a context object and another url. These
are added to the queue of jobs to scrape.

Good friends of ``ragstoriches`` are the `urlparse.urljoin
<http://docs.python.org/2/library/urlparse.html#urlparse.urljoin>`_ function
and `BeautifulSoup4 <https://beautiful-soup-4.readthedocs.org/en/latest/>`_.


Usage as a library
------------------

You can use ragstoriches as a library as well by not using the commandline
tools but simply importing a scraper and running it with the ``scrape()``
method. Remember to monkey-patch using gevent first.

See the source files for details, as there is not that much documentation
available at this point.
