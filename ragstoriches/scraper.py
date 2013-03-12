#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import inspect
import traceback

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

                if not inspect.isgeneratorfunction(scraper):
                    scope.inject_and_call(scraper, url=url)
                else:
                    for new_job in scope.inject_and_call(scraper, url=url):
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
