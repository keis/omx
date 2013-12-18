#!/usr/bin/env python2

from omx.decl import path, target
from omx.target import Target, Singleton
from hamcrest import assert_that, equal_to
import unittest


def test_tagname():
    assert_that(path('foo'), equal_to(['foo']))


def test_split():
    assert_that(path('foo/bar'), equal_to(['foo', 'bar']))


def test_split_trailing():
    assert_that(path('foo/bar/'), equal_to(['foo', 'bar']))


def test_attribute():
    assert_that(path('@boo'), equal_to(['@boo']))


def test_default():
    assert_that(
        path('foo', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['{http://default}foo'])
    )


def test_default_split():
    assert_that(
        path('foo/bar', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['{http://default}foo', '{http://default}bar'])
    )


def test_default_attrib():
    assert_that(
        path('@boo', references={
            '': 'http://test'
        }),
        equal_to(['@boo'])
    )


def test_explicit():
    assert_that(
        path('x:foo', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['{http://test}foo'])
    )


def test_explicit_split():
    assert_that(
        path('x:foo/bar', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['{http://test}foo', '{http://default}bar'])
    )


def test_explicit_attrib():
    assert_that(
        path('@x:boo', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['@{http://test}boo'])
    )


def test_explicit_nons():
    assert_that(
        path(':boo', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['boo'])
    )


def test_explicit_nons_attrib():
    assert_that(
        path('@:boo', references={
            '': 'http://default',
            'x': 'http://test'
        }),
        equal_to(['@boo'])
    )


def test_simple_target():
    assert_that(target('foo'), equal_to((Target, [['foo']])))


def test_singleton_target():
    assert_that(target('@foo'), equal_to((Singleton, [['@foo']])))


def test_multi_attribute_target():
    assert_that(target('@foo|@bar'),
                equal_to((Target, [['@foo'], ['@bar']])))


def test_target_path_list():
    assert_that(target(['foo', 'bar/baz']),
                equal_to((Target, [['foo'], ['bar', 'baz']])))
