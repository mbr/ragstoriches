#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import inspect
import traceback
from urlparse import urljoin
import sys

from gevent.pool import Pool
from gevent.queue import JoinableQueue
import logbook
import requests

from errors import *
from injection import Scope, get_default_args

log = logbook.Logger('ragstoriches')


class Job(object):
    def __init__(self, parent, scraper_name, url=None, parent_scope=None,
                 attempt=0):
        self.scraper = parent.scrapers[scraper_name]
        self.scope = parent_scope.new_child() if parent_scope else Scope()
        self.attempt = attempt
        self.parent = parent

        # get default url
        def_args = get_default_args(self.scraper)
        if 'url' in def_args:
            self.scope['url'] = def_args['url']

        # passed-in url
        if url != None:
            self.scope['url'] = url

        # set up log
        self.scope['log'] = logbook.Logger('%s.%s' % (
            self.parent.name, scraper_name
        ))


    @property
    def log(self):
        return self.scope['log']

    @property
    def url(self):
        return self.scope['url']

    def from_yield(self, yield_val):
        scope = self.scope.new_child()

        if len(yield_val) == 3:
            scraper_name, rel_url, new_context = yield_val
            scope.update(new_context)
        elif len(yield_val) == 2:
            scraper_name, rel_url = yield_val

        return self.__class__(
            self.parent,
            scraper_name,
            urljoin(self.url, rel_url),
            scope
        )

    def retry(self):
        self.attempt += 1
        return self

    def run(self):
        self.log.info(self.url)
        if not inspect.isgeneratorfunction(self.scraper):
            self.scope.inject_and_call(self.scraper)
            return
            yield
        else:
            for val in self.scope.inject_and_call(self.scraper):
                yield val

    def __str__(self):
        return 'Job(%d)<%s:%s>' % (self.attempt, self.scraper_name, self.url)


class Scraper(object):
    def __init__(self, name='Unnamed Scraper'):
        self.name = name
        self.scrapers = {}

    def __call__(self, f):
        self.scrapers[f.__name__] = f
        return f

    def scrape(self, url=None, scraper_name='index',
               session=None, concurrency=None, receivers=[],
               initial_scope={}, exception_handler=None):
        pool = Pool(concurrency+2 if concurrency != None else None)
        job_queue = JoinableQueue()
        data_queue = JoinableQueue()

        scope = Scope()
        scope['log'] = logbook.Logger(self.name)
        scope['push_data'] = lambda name, data:\
            data_queue.put((name, data))
        scope['requests'] = session or requests.Session()
        scope.update(initial_scope)

        job_queue.put(Job(self, scraper_name, url, scope))

        aborted = False

        def run_job(job):
            # runs a single job in the current greenlet
            try:
                # setup new log
                for val in job.run():
                    job_queue.put(job.from_yield(val))
            except CriticalError as e:
                job.log.critical(e)
                job.log.debug(traceback.format_exc())
                job.log.debug('Aborting scrape...')
                aborted = True
            except Exception as e:
                job.log.error('Error handling job "%s" "%s": %s' %
                                       (scraper_name, url, e))
                job.log.debug(traceback.format_exc())
                if exception_handler:
                    exception_handler(sys.exc_info())
            finally:
                job_queue.task_done()

        def job_spawner():
            # using the pool, spawns a new job for every job in the queue
            while not aborted:
                job = job_queue.get()
                if None == job:
                    break
                pool.spawn(run_job, job)

        def receiver_spawner():
            while not aborted:
                record = data_queue.get()
                if None == record:
                    break

                for receiver in receivers:
                    pool.spawn(receiver.process, record, scope)

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

        # now perform all post-processing
        for receiver in receivers:
            if receiver._post_process:
                post_scope = scope.new_child()
                post_scope['log'] = logbook.Logger('%s-post_process')
                post_scope.inject_and_call(receiver._post_process)
