#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ragstoriches.receiver import Receiver

receiver = Receiver(__name__)


@receiver
def posting(**kwargs):
    print 'New posting: %r' % kwargs
