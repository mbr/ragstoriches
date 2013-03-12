#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ragstoriches.injection import Scope


def test_works_like_dict():
    scope = Scope()
    scope['bar'] = 'foo'
    scope['foo'] = 'baz'

    assert scope['bar'] == 'foo'
    assert scope['foo'] == 'baz'


def test_call_simple():
    def foo(a, b, c='xx'):
        assert a == 'val_a'
        assert b == 'val_b'
        assert c == 'val_c'

    scope = Scope()

    scope.inject_and_call(foo, 'val_a', 'val_b', 'val_c')
    scope.inject_and_call(foo, b='val_b', c='val_c', a='val_a')


def test_automatic_injection():
    def foo(d, e, f):
        assert d == 'val_d'
        assert e == 'val_e'
        assert f == 'val_f'

    scope = Scope()
    scope['e'] = 'val_e'
    scope['f'] = 'val_f'

    scope.inject_and_call(foo, 'val_d')


def test_overwrite_works():
    def foo(d, e, f):
        assert d == 'val_d'
        assert e == 'val_e'
        assert f == 'val_f'

    scope = Scope()
    scope['d'] = 'bad'
    scope['e'] = 'also bad'
    scope['f'] = 'val_f'

    scope.inject_and_call(foo, 'val_d', e='val_e')
