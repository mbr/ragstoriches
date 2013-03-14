#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

def export(obj, name=None):
    mod = inspect.getmodule(inspect.currentframe().f_back)

    if not hasattr(mod, '_rr_export'):
        mod._rr_export = {}
    mod._rr_export[name or obj.__name__] = obj

    return obj
