#!/usr/bin/env python2

import unittest

from .. import OMX, Template
from ..core import OMXState, TemplateData


class Singleton(unittest.TestCase):
	def test_auto(self):
		foot = Template('foo',
			('@bar', 'text()', 'baz/text()', 'baz/@baz'))
		omx = OMX((foot,), 'foo')
		state = OMXState(omx)
		data = TemplateData(foot, state)

		self.assertTrue(data.values[0].singleton)
		self.assertTrue(data.values[1].singleton)
		self.assertFalse(data.values[2].singleton)
		self.assertFalse(data.values[3].singleton)


class Iterate(unittest.TestCase):
	omx = OMX((), 'foo')

	def setUp(self):
		self.state = OMXState(self.omx)

	def test_deep(self):
		foo = self.state.add_target('/base/foo', 'foo')
		bar = self.state.add_target('/base/foo/bar', 'bar')
		baz = self.state.add_target('/base/foo/bar/baz', 'baz')

		i = self.state.itertargets()

		a = next(i)
		self.assertEqual(a[1], None)

		b = next(i)
		self.assertEqual(b[1], foo)

		c = next(i)
		self.assertEqual(c[1], bar)

		d = next(i)
		self.assertEqual(d[1], baz)

		e = next(i)
		self.assertEqual(e[1], baz)

	def test_wide(self):
		foo = self.state.add_target('/base/foo', 'foo')
		bar = self.state.add_target('/base/bar', 'bar')
		baz = self.state.add_target('/base/baz', 'baz')

		i = self.state.itertargets()
		path, t = next(i)
		self.assertEqual(t, None)

		visited = set()
		for path, t in i:
			visited.add(t)
			self.state.remove_target(path)

		expected = {foo, bar, baz, None}
		self.assertEqual(visited, expected)
	

class Add(unittest.TestCase):
	omx = OMX((), 'foo')

	def setUp(self):
		self.state = OMXState(self.omx)

	def test_duplicate(self):
		foo = self.state.add_target('/base/foo', 'foo')
		self.assertRaises(Exception, self.state.add_target, '/base/foo', 'foo')

	def test_child(self):
		foo = self.state.add_target('/base/foo', 'foo')
		bar = self.state.add_target('/base/foo/bar', 'bar')

		self.assertTrue(self.state.get_target('/base') is None)
		self.assertTrue(self.state.get_target('/base/foo') is foo)
		self.assertTrue(self.state.get_target('/base/foo/bar') is bar)

	def test_parent(self):
		bar = self.state.add_target('/base/foo/bar', 'bar')
		foo = self.state.add_target('/base/foo', 'foo')

		self.assertTrue(self.state.get_target('/base') is None)
		self.assertTrue(self.state.get_target('/base/foo') is foo)
		self.assertTrue(self.state.get_target('/base/foo/bar') is bar)

	def test_intermediate(self):
		foo = self.state.add_target('/base/foo/foo/foo', 'foo')

		self.assertTrue(self.state.get_target('/base') is None)
		self.assertTrue(self.state.get_target('/base/foo') is None)
		self.assertTrue(self.state.get_target('/base/foo/foo') is None)
		self.assertTrue(self.state.get_target('/base/foo/foo/foo') is foo)


class Children(unittest.TestCase):
	omx = OMX((), 'foo')

	def setUp(self):
		self.state = OMXState(self.omx)

	def test_basic(self):
		self.state.add_target('/base/foo', 'foo')
		self.state.add_target('/base/bar', 'bar')

		c = self.state.children('/base')
		c = list(c)
		self.assertTrue(len(c), 2)

	def test_no_children(self):
		self.state.add_target('/base/foo', 'foo')
		self.state.add_target('/base/bar', 'bar')

		c = self.state.children('/base/foo')
		self.assertEqual(list(c), [])

	def test_level(self):
		self.state.add_target('/base/foo', 'foo')
		self.state.add_target('/base/bar', 'bar')
		self.state.add_target('/test', 'test')

		c = self.state.children('/test')
		self.assertEqual(list(c), [])

	def test_invalid(self):
		self.state.add_target('/base/foo', 'foo')
		self.state.add_target('/base/bar', 'bar')

		self.assertRaises(KeyError, list, self.state.children('/test'))

if __name__ == '__main__':
	unittest.main()
