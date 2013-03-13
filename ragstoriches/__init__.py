#!/usr/bin/env python
# -*- coding: utf-8 -*-

def export(func):
    func._ragstoriches_export = func.__name__
    return func
