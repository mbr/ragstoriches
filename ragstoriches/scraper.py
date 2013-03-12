#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import inspect
import traceback
from urlparse import urljoin


from gevent.pool import Pool
from gevent.queue import JoinableQueue
import logbook
import requests

from injection import Scope, get_default_args

log = logbook.Logger('ragstoriches')


class Scraper(object):
    def __init__(self, name='Unnamed Scraper'):
        self.scrapers = {}

    def scraper(self, f):
        self.scrapers[f.__name__] = f
        return f

    def scrape(self, url=None, scraper_name='index', context=None,
               session=None, concurrency=None):
        pool = Pool(concurrency+1 if concurrency != None else None)
        job_queue = JoinableQueue()

        scope = Scope()
        scope['requests'] = session or requests.Session()
        scope['context'] = context or {}

        job_queue.put((scraper_name, url, context))

        def run_job(job):
            # runs a single job in the current greenlet
            if not len(job) == 3:
                log.error('Malformed job (must be 3-tuple): %r' % (job,))
                job_queue.task_done()
                return

            scraper_name, url, context = job
            job_scope = scope.new_child()
            job_scope['context'] = context
            try:
                scraper = self.scrapers[scraper_name]

                # retrieve url from default arguments
                if not url:
                    defargs = get_default_args(scraper)
                    if not 'url' in defargs:
                        raise TypeError('Scraper %r does not have a default '
                                        'value for \'url\' and none was '
                                        'supplied' % scraper)

                    url = defargs['url']


                log.debug("Calling scraper %s on %s'" % (
                    scraper.__name__, url
                ))
                log.debug('Queue size: %d' % job_queue.qsize())
                log.info(url)

                def parse_yield(scraper_name, rel_url=url, new_context={}):
                    return scraper_name, urljoin(url, rel_url), new_context

                if not inspect.isgeneratorfunction(scraper):
                    job_scope.inject_and_call(scraper, url=url)
                else:
                    for new_job in job_scope.inject_and_call(scraper, url=url):
                        job_queue.put(parse_yield(*new_job))
            except Exception as e:
                log.error('Error handling job "%s" "%s": %s' %
                              (scraper_name, url, e))
                log.debug(traceback.format_exc())
            finally:
                job_queue.task_done()

        def spawner():
            # using the pool, spawns a new job for every job in the queue
            while True:
                job = job_queue.get()
                if None == job:
                    break
                pool.spawn(run_job, job)

        spawner_greenlet = pool.spawn(spawner)

        # join queue
        job_queue.join()

        # tell spawner to exit
        job_queue.put(None)
        pool.join()
