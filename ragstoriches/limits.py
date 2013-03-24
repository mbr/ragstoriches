#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent.coros import RLock
from gevent import sleep
from time import time


class TicketGenerator(object):
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

                # needs more tickets
                if delay:
                    sleep(delay)

            self._tickets -= n
