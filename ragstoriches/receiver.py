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

    def process(self, record, scope):
        receiver_name, data = record
        log.debug('receiver %s processing record on %s' % (
            receiver_name, self.name))
        call_scope = scope.new_child()
        call_scope['result'] = data

        if not receiver_name in self.receivers:
            call_scope['data_type'] = receiver_name

        return call_scope.inject_and_call(
            self.receivers.get(receiver_name, 'any')
        )
