#!/usr/bin/env python
# -*- coding: utf-8 -*-

from stuf.collects import ChainMap
import inspect

class Scope(ChainMap):
    def inject_and_call(self, func, *args, **kwargs):
        func_args = inspect.getargs(func.func_code)

        call_kwargs = kwargs.copy()

        # adds all arguments that have not been passed via *args or **kwargs
        # as a keyword argument from Scope
        for arg_name in func_args.args[len(args):]:
            if not arg_name in call_kwargs:
                call_kwargs[arg_name] = self[arg_name]

        return func(*args, **call_kwargs)
