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
        self.name = name
        self.scrapers = {}

    def __call__(self, f):
        self.scrapers[f.__name__] = f
        return f

    def scrape(self, url=None, scraper_name='index',
               session=None, concurrency=None, receivers=[],
               initial_scope={}):
        pool = Pool(concurrency+2 if concurrency != None else None)
        job_queue = JoinableQueue()
        data_queue = JoinableQueue()

        scope = Scope()
        scope['log'] = logbook.Logger(self.name)
        scope.update(initial_scope)

        scraper_scope = scope.new_child()
        scraper_scope['requests'] = session or requests.Session()
        scraper_scope['data'] = lambda name, *args, **kwargs:\
            data_queue.put((name, args, kwargs))

        receiver_scope = scope.new_child()

        job_queue.put((scraper_name, url, scraper_scope))

        def run_job(job):
            # runs a single job in the current greenlet
            if not len(job) == 3:
                job_scope['log'].error(
                    'Malformed job (must be 3-tuple): %r' % (job,)
                )
                job_queue.task_done()
                return

            scraper_name, url, job_scope = job
            try:
                scraper = self.scrapers[scraper_name]

                job_scope['log'].debug("Calling scraper %s on %s'" % (
                    scraper.__name__, url
                ))
                job_scope['log'].debug('Queue size: %d' % job_queue.qsize())

                # setup new log
                job_scope = job_scope.new_child()
                job_scope['log'] = logbook.Logger('%s.%s' % (
                   self.name, scraper_name
                ))

                job_scope['log'].info(url)

                if url:
                    job_scope['url'] = url

                def parse_yield(scraper_name, rel_url=url, new_context={}):
                    scope = job_scope.new_child()
                    scope.update(new_context)
                    return scraper_name, urljoin(url, rel_url), scope

                if not inspect.isgeneratorfunction(scraper):
                    job_scope.inject_and_call(scraper)
                else:
                    for new_job in job_scope.inject_and_call(scraper):
                        job_queue.put(parse_yield(*new_job))
            except Exception as e:
                job_scope['log'].error('Error handling job "%s" "%s": %s' %
                                       (scraper_name, url, e))
                job_scope['log'].debug(traceback.format_exc())
            finally:
                job_queue.task_done()

        def job_spawner():
            # using the pool, spawns a new job for every job in the queue
            while True:
                job = job_queue.get()
                if None == job:
                    break
                pool.spawn(run_job, job)

        def receiver_spawner():
            while True:
                record = data_queue.get()
                if None == record:
                    break

                for receiver in receivers:
                    pool.spawn(receiver.process, record, receiver_scope)

                data_queue.task_done()

        spawner_greenlet = pool.spawn(job_spawner)
        receiver_greenlet = pool.spawn(receiver_spawner)

        # join queue
        job_queue.join()
        data_queue.join()

        # tell spawner to exit
        job_queue.put(None)
        data_queue.put(None)
        pool.join()
