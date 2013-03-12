#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ragstoriches.injection import Scope, get_default_args


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


def test_get_default_args():
    def f1(a, b, c):
        pass

    def f2(a, b='b_def', c='c_def'):
        pass

    def f3(a, *args, **kwargs):
        pass

    def f4(a='a_def', b='b_def'):
        pass

    def f5():
        pass

    assert get_default_args(f1) == {}
    assert get_default_args(f2) == { 'b': 'b_def', 'c': 'c_def' }
    assert get_default_args(f3) == {}
    assert get_default_args(f4) == { 'a': 'a_def', 'b': 'b_def'}
    assert get_default_args(f5) == {}
