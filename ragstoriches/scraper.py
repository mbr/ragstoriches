#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import inspect
import traceback

from gevent.pool import Pool
from gevent.queue import JoinableQueue
import logbook
import requests

log = logbook.Logger('ragstoriches')


class Scraper(object):
    def __init__(self, name='Unnamed Scraper'):
        self.scrapers = {}

    def scraper(self, f):
        if not inspect.isgeneratorfunction(f):
            @functools.wraps(f)
            def _(*args, **kwargs):
                yield f(*args, **kwargs)
        else:
            _ = f


        self.scrapers[_.__name__] = _
        return _

    def scrape(self, url=None, scraper_name='index', context=None,
               session=None, concurrency=None):
        pool = Pool(concurrency+1 if concurrency != None else None)
        job_queue = JoinableQueue()
        context = context or {}
        session = session or requests.Session()

        job_queue.put((scraper_name, context, url))

        def run_job(job):
            # runs a single job in the current greenlet
            if not len(job) == 3:
                log.error('Malformed job (must be 3-tuple): %r' % (job,))
                job_queue.task_done()
                return

            scraper_name, context, url = job
            try:
                scraper = self.scrapers[scraper_name]

                if not url:
                    log.debug('Using default argument for url')
                    fargs, _, _, fdefaults = inspect.getargspec(scraper)
                    if not fdefaults:
                        raise TypeError('Scraper %r does not have an argument '
                                        '\'url\'.' % scraper)
                    fargs_with_defaults = fargs[-len(fdefaults):]

                    if not 'url' in fargs_with_defaults:
                        raise TypeError('Scraper %r does not have a default '
                                        'value for \'url\'' % scraper)

                    url = fdefaults[fargs_with_defaults.index('url')]


                log.debug("Calling scraper %s on %s with context %r'" % (
                    scraper.__name__, url, context
                ))
                log.info(url)
                log.debug('Queue size: %d' % job_queue.qsize())

                for new_job in scraper(session, context, url):
                    if new_job:
                        job_queue.put(new_job)
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