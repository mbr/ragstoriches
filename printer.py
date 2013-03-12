#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ragstoriches.receiver import Receiver

receiver = Receiver(__name__)

@receiver
def any(name, *args, **kwargs):
    print '%s%r: %r' % (name, args, kwargs)
