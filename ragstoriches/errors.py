#!/usr/bin/env python
# -*- coding: utf-8 -*-

class RagsToRichesError(Exception):
    pass


class TemporaryError(RagsToRichesError):
    pass


class CapacityError(TemporaryError):
    pass


class PermanentError(RagsToRichesError):
    pass


class CriticalError(RagsToRichesError):
    pass
