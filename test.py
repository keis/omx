#!/usr/bin/env python2

import unittest

from omx import OMX, Template
from omx import OMXState, TemplateData


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

	def test_empty(self):
		# dunno what should happen
		t = self.state.next_target(None)

	def test_deep(self):
		foo = self.state.add_target('/base/foo', 'foo')
		bar = self.state.add_target('/base/foo/bar', 'bar')
		baz = self.state.add_target('/base/foo/bar/baz', 'baz')

		a = self.state.next_target(None)
		self.assertEquals(a[1], None)

		b = self.state.next_target(a[0])
		self.assertEquals(b[1], foo)

		c = self.state.next_target(b[0])
		self.assertEquals(c[1], bar)

		d = self.state.next_target(c[0])
		self.assertEquals(d[1], baz)

		e = self.state.next_target(d[0])
		self.assertEquals(e[1], baz)

	def test_wide(self):
		foo = self.state.add_target('/base/foo', 'foo')
		bar = self.state.add_target('/base/bar', 'bar')
		baz = self.state.add_target('/base/baz', 'baz')

		visited = []

		path, t = self.state.next_target(None)
		self.assertEquals(t, None)
		lpath = list(path)

		while self.state.has_target():
			path, t = self.state.next_target(lpath)
			visited.append(t)
			lpath = list(path)
			lpath.pop()
			self.state.remove_target(path)

		visited.sort()
		expected = [foo, bar, baz, None]
		expected.sort()
		self.assertEquals(visited, expected)
	

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

		self.assertTrue(len(self.state._OMXState__targets), 4)
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

		c = self.state.children('/test')
		self.assertEqual(list(c), [])

if __name__ == '__main__':
	unittest.main()
