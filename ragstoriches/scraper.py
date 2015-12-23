#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import time
import traceback
from urlparse import urljoin
import sys

from gevent.pool import Pool
from gevent.coros import RLock
from gevent.queue import JoinableQueue
from gevent.local import local
import logbook
import requests
from requests.adapters import HTTPAdapter

from errors import *
from injection import Scope, get_default_args
from limits import TicketGenerator

log = logbook.Logger('ragstoriches')

glocal = local()


class JobQueue(object):
    def __init__(self):
        self._qlock = Condition(RLock())
        self._all_done = Condition(RLock())
        self._jobs = []
        self._count = 0

    def get(self):
        with self._qlock:
            while True:
                if not self._jobs:
                    # queue is empty, wait until there is a job
                    self._jobs.wait()

                # now there's at least one job
                job = self._jobs[0]

                if not job.execution_time:
                    return heapq.heappop(self._jobs)

                cur_time = time.time()
                if job.execution_time <= cur_time:
                    return heapq.heappop(self._jobs)

                # there is a job, but we can't execute it right away
                # wait until there's a new job or enough time has passed
                self._qlock.wait(job.execution_time - cur_time)

    def join(self):
        with self._all_done:
            self._all_done().wait()

    def put(self, job):
        with self._qlock:
            heapq.heappush(self._jobs, job)

            # increase job count
            self._count += 1

            # new data
            self._qlock.notify()

    def task_done(self):
        with self._qlock:
            self._count -= 1

            if self._count == 0:
                with self._all_done:
                    self._all_done().notifyAll()


class NullJob(object):
    execution_time = 0

    def __lt__(self, them):
        return True


class Job(object):
    def __init__(self,
                 parent,
                 scraper_name,
                 url=None,
                 parent_scope=None,
                 attempt=0,
                 execution_time=None,
                 priority=None):
        self.scraper = parent.scrapers[scraper_name]
        self.scraper_name = scraper_name
        self.scope = parent_scope.new_child() if parent_scope else Scope()
        self.attempt = attempt
        self.parent = parent

        # get default url
        def_args = get_default_args(self.scraper)
        if 'url' in def_args:
            self.scope['url'] = def_args['url']

        # passed-in url
        if url is not None:
            self.scope['url'] = url

        # set up log
        self.scope['log'] = logbook.Logger('%s.%s' % (self.parent.name,
                                                      scraper_name))

    def __lt__(self, them):
        if isinstance(them, NullJob):
            return False

        if (self.execution_time or 0) == (them.execution_time or 0):
            return (self.priority or 0) > (them.priority or 0)
        return (self.execution_time or 0) < (them.execution_time or 0)

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

        return self.__class__(self.parent, scraper_name,
                              urljoin(self.url, rel_url), scope)

    def retry(self):
        self.attempt += 1
        return self

    def run(self):
        glocal.log = self.scope['log']
        if not inspect.isgeneratorfunction(self.scraper):
            self.scope.inject_and_call(self.scraper)
            return
            yield
        else:
            for val in self.scope.inject_and_call(self.scraper):
                yield val

    def __str__(self):
        return 'Job(%d)<%s:%s>' % (self.attempt, self.scraper_name, self.url)


class TicketBoundHTTPAdapter(HTTPAdapter):
    def __init__(self, ticket_gen, *args, **kwargs):
        super(TicketBoundHTTPAdapter, self).__init__(*args, **kwargs)
        self.ticket_gen = ticket_gen

    def send(self, *args, **kwargs):
        # obtain a ticket
        self.ticket_gen.get()

        # then send
        return super(TicketBoundHTTPAdapter, self).send(*args, **kwargs)


class Scraper(object):
    def __init__(self, name='Unnamed Scraper'):
        self.name = name
        self.scrapers = {}

    def __call__(self, f):
        self.scrapers[f.__name__] = f
        return f

    def scrape(self,
               url=None,
               scraper_name='index',
               session=None,
               burst_limit=None,
               rate_limit=None,
               receivers=[],
               initial_scope={},
               exception_handler=None):
        pool = Pool(10000)  # almost no limit, limit connections instead
        job_queue = JoinableQueue()
        data_queue = JoinableQueue()

        scope = Scope()
        scope['log'] = logbook.Logger(self.name)
        scope['push_data'] = lambda name, data:\
            data_queue.put((name, data))

        rs = session or requests.Session()
        rs.hooks['response'] = lambda r: glocal.log.info(r.url)
        cticket_gen = TicketGenerator(rate_limit, burst_limit)
        adapter = TicketBoundHTTPAdapter(cticket_gen)
        rs.mount('http://', adapter)
        rs.mount('https://', adapter)
        scope['requests'] = rs
        scope.update(initial_scope)

        job_queue.put(Job(self, scraper_name, url, scope))

        aborted = False

        def run_job(job):
            # runs a single job in the current greenlet
            try:
                # setup new log
                for val in job.run():
                    job_queue.put(job.from_yield(val))
            except CapacityError as e:
                job.log.warning('CapacityError: %s, backing off')
                job.log.debug(traceback.format_exc())
                # FIXME: throttle
            except TemporaryError as e:
                job.log.warning('Temporary failure on %s, ' 'rescheduling')
                job.log.debug(traceback.format_exc())
                job_queue.put(job.retry())
                # FIXME: add limit for retries
            except PermanentError as e:
                job.log.error(e)
                job.log.debug(traceback.format_exc())
            except CriticalError as e:
                job.log.critical(e)
                job.log.debug(traceback.format_exc())
                job.log.debug('Aborting scrape...')
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
                if job is None:
                    break
                pool.spawn(run_job, job)

        def receiver_spawner():
            while not aborted:
                record = data_queue.get()
                if record is None:
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
