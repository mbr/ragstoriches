#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logbook

log = logbook.Logger('ragstoriches.receiver')

class Receiver(object):
    def __init__(self, name='Unnamed Receiver'):
        self.name = name
        self.receivers = {}

    def __call__(self, f):
        self.receivers[f.__name__] = f
        return f

    def process(self, receiver_name, rargs, rkwargs, scope):
        log.debug('receiver %s processing record on %s' % (
            receiver_name, self.name))

        if not receiver_name in self.receivers:
            return scope.inject_and_call(
                self.receivers['any'], receiver_name, *rargs, **rkwargs
            )

        return scope.inject_and_call(
                self.receivers[receiver_name](*rargs, **rkwargs)
            )
