#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent.coros import RLock
from gevent import sleep
from time import time


class TicketGenerator(object):
    def __init__(self, interval=1.0, max=0, initial=None):
        if initial == None:
            initial = max

        if not max:
            self.tickets = Semaphore(initial)
        else:
            self.tickets = BoundedSemaphore(max)

        for i in xrange(max-initial):
            self.tickets.acquire()  # reduce to correct value

        self.interval = float(interval)

    def get(self, n=1):
        for i in xrange(n):
            self.tickets.acquire()

    def run(self):
        prev = time()
        credits = 0

        while True:
            sleep(self.interval)
            cur = time()

            credits += (cur - prev)/self.interval

            try:
                while credits >= 1:
                    credits -= 1
                    self.tickets.release()
            except ValueError:
                # semaphore is 'full'
                credits = 0
            finally:
                prev = cur


class TicketGenerator2(object):
    def __init__(self, tps=1.0, max=None, initial=None):
        self.last_update = time()
        self._lock = RLock()
        self._tickets = initial or max or 0

        self.tps = tps
        self.ticket_max = max

    def _update_tickets(self):
        cur = time()
        self._tickets += (cur - self.last_update) * self.tps

        # restrict to ticket max
        if self.ticket_max:
            self._tickets = min(self.ticket_max, self._tickets)

        self.last_update = cur

    def get(self, n=1):
        if self.ticket_max and n > self.ticket_max:
            raise ValueError('Ticket maximum is %s' % self.ticket_max)

        with self._lock:
            self._update_tickets()

            if self._tickets < n:
                delay = self.last_update + (n/float(self.tps)) - time()
                print "need to wait", delay, "to go from", self._tickets, "to",\
                n

                # needs more tickets
                if delay:
                    sleep(delay)

            self._tickets -= n
