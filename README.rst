from ragstoriches
=================

*ragstoriches* is a combined library/framework to ease writing web scrapers
using gevent and requests.

A simple example to tell the story:

.. code-block:: python

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
   def posting(requests, url):
       html = document_fromstring(requests.get(url).content)

       title = html.cssselect('.postingtitle')[0].text.strip()
       id = re.findall(r'\d+', html.cssselect('div.postinginfos p')[0].text)[0]
       date = html.cssselect('.postinginfos date')[0].text.strip()
       body = html.cssselect('#postingbody')[0].text_content().strip()

       print title
       print '=' * len(title)
       print 'post *%s*, posted on %s' % (id, date)
       print body
       print

Install the library and `lxml <http://lxml.de>`_, `cssselect
<http://pythonhosted.org/cssselect/>`_ using ``pip install
ragstoriches lxml cssselect``, then save the above as ``craigs.py``,
finally run with ``ragstoriches craigs.py``.

You will get a bunch of jumbled output, so next step is redirecting ``stdout``
to a file::

   ragstoriches craigs.py > output.md

Try giving different urls for this scraper on the command-line:

.. code-block:: sh

   ragstoriches craigs.py http://newyork.craigslist.org/mnh/acc/  > output.md  # hustle
   ragstoriches craigs.py http://orangecounty.craigslist.org/wet/ > output.md  # writing OC
   ragstoriches craigs.py http://seattle.craigslist.org/w4m/      > output.md  # sleepless in seattle

There are a lot of commandline-options available, see ``ragstoriches --help``
for a list.


Parsing HTML
------------

*ragstoriches* works with almost any kind of HTML-parsing library, while using
lxml is recommend, you can easily use `BeautifulSoup4
<http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_ or another library
(lxml, in my tests, turned out to be about five times as fast as BeautifulSoup
though and the CSS-like selectors are a joy to use).


Writing scrapers
----------------

A scraper module consists of some initialization code and a number of
subscrapers. Scraping starts by calling the a scraper named ``index`` (see the
example above).

Scrapers make use of dependency injection - the argument names are looked up in
a scope and filled with the relevant instance. This means that if your
subscraper takes an argument called ``url``, it will always be the URL to
scrape, ``requests`` always a pool instance and so on.

The following predefined injections are available:

* ``requests``: A ``requests`` session. Can be treated like the top-level API
  of `requests <http://python-requests.org>`_. As long as you use it for
  fetching webpages, you never have to worry about blocking or exceeding
  concurrency limits.
* ``url``: The url to scrape and parse.
* ``data``: A callback for passing data out of the scraper. See the example
  below.

Return values of scrapers are ignored. However, if a scraper is a generater
(i.e. contains a yield statement), it should yield tuples of ``subscraper_name,
url`` or ``subscraper_name, url, context``. These
are added to the queue of jobs to scrape, the contents of ``context`` are added
to the scope for all following subscraper calls.

The ``url``-yield is ``urlparse.urljoin``-ed onto the ``url`` passed into the
scraper, this means that you do not have to worry about relative links, they
just work.


Using receivers
---------------

You can decouple scraping/parsing and the actual processing of the resulting
data by using receivers. Let's rewrite the example above a slight bit by
replacing the second function with this:

.. code-block:: python

   @scraper
   def posting(requests, url, data):
       html = document_fromstring(requests.get(url).content)

       data('posting',
           title=html.cssselect('.postingtitle')[0].text.strip(),
           id=re.findall(r'\d+', html.cssselect('div.postinginfos p')[0].text)[0],
           date=html.cssselect('.postinginfos date')[0].text.strip(),
           body=html.cssselect('#postingbody')[0].text_content().strip(),
       )

Two differences: We inject ``data`` as an argument and instead of printing our
data, we pass it to the new callable.

When you call ``data``, the first argument is the name of a subreceiver and
everything passed into it gets passed on to every receiver loaded in a
dictionary called ``result``. We didn't load any receivers, so running the
scraper will do nothing but fill up the data-queue.

To rectify this situation, put the following into a file called ``printer.py``:

.. code-block:: python

   from ragstoriches.receiver import Receiver

   receiver = Receiver(__name__)


   @receiver
   def posting(result):
       print 'New posting: %r' % result

Afterwards, run ``ragstoriches -q craigs.py printer.py``. The result will be
that the receiver prints the extracted data to stdout, nicely decoupling
extraction and processing.

Caching
-------

You can transparently cache downloaded data, this is especially useful when
developing. Simply pass ``--cache some_name`` to ``ragstoriches``, which will
use `requests-cache <https://github.com/reclosedev/requests-cache>`_ for
caching.


Usage as a library
------------------

You can use ragstoriches as a library (instead of as a framework, by using the
commandline utilities) as well, but there is no detailed documentation. Drop me
a line if this is important for you.
