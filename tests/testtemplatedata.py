#!/usr/bin/env python2

import unittest
from mock import Mock

from omx import template
from omx.core import TemplateData, Target


@template('foo', ('aa', 'bb'))
def positional(aa, bb):
    return (aa, bb)


class TestCreate(unittest.TestCase):
    def setUp(self):
        self.state = Mock()
        self.state.add_target = lambda path, name: Target(name, False)

    def test_positional(self):
        t = TemplateData(positional, self.state)
        self.assertEqual(len(t.values), 2)
        a, b = t.values
        self.assertEqual(None, a.name)
        a.add('spam')
        self.assertEqual(None, b.name)
        b.add('egg')
        r = t.create()
        self.assertEqual((['spam'], ['egg']), r)
