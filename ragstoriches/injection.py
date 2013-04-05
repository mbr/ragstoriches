#!/usr/bin/env python
# -*- coding: utf-8 -*-

from stuf.collects import ChainMap
import inspect

class Scope(ChainMap):
    def inject_and_call(self, func, *args, **kwargs):
        func_args = inspect.getargspec(func)

        call_kwargs = kwargs.copy()

        # adds all arguments that have not been passed via *args or **kwargs
        # as a keyword argument from Scope
        for arg_name in func_args.args[len(args):]:
            if not arg_name in call_kwargs:
                if not arg_name in self:
                    raise TypeError('Missing argument %s, neither in scope '
                                    'nor defaults.')
                call_kwargs[arg_name] = self[arg_name]

        return func(*args, **call_kwargs)


def get_default_args(func):
    argspec = inspect.getargspec(func)

    if not argspec.defaults:
        return {}
    return dict(zip(reversed(argspec.args), reversed(argspec.defaults)))
