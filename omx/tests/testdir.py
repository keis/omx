#!/usr/bin/env python2

import unittest

from ..core import Target, TargetDir, traverse

class Position(unittest.TestCase):
	def setUp(self):
		self.dir = TargetDir()

	def test_empty(self):
		self.assertTrue(self.dir.empty)

	def test_empty_path(self):
		self.dir.add(('foo',), 'foo')
		self.assertEqual(self.dir.get(()), None)

	def test_nonexistant(self):
		self.assertRaises(KeyError, self.dir.get, ('what', 'ever'))

	def test_simple(self):
		foo = self.dir.add(('foo',), 'foo')
		self.assertEqual(foo, 'foo')
		self.assertFalse(self.dir.empty)
		self.assertEqual(self.dir.get(('foo',)), foo)

	def test_duplicate(self):
		foo = self.dir.add(('base', 'foo'), 'foo')
		self.assertEqual(foo, 'foo')
		self.assertFalse(self.dir.empty)
		self.assertRaises(Exception, self.dir.add, ('base', 'foo'), 'foo')

	def test_child(self):
		foo = self.dir.add(('base', 'foo'), 'foo')
		bar = self.dir.add(('base', 'foo', 'bar'), 'bar')
		
		self.assertEqual(foo, 'foo')
		self.assertEqual(bar, 'bar')
		self.assertFalse(self.dir.empty)
		self.assertIs(self.dir.get(('base',)), None)
		self.assertIs(self.dir.get(('base', 'foo')), foo)
		self.assertIs(self.dir.get(('base', 'foo', 'bar')), bar)

	def test_parent(self):
		bar = self.dir.add(('base', 'foo', 'bar'), 'bar')
		foo = self.dir.add(('base', 'foo'), 'foo')

		self.assertEqual(foo, 'foo')
		self.assertEqual(bar, 'bar')
		self.assertFalse(self.dir.empty)
		self.assertIs(self.dir.get(('base',)), None)
		self.assertIs(self.dir.get(('base', 'foo')), foo)
		self.assertIs(self.dir.get(('base', 'foo', 'bar')), bar)

	def test_intermediate(self):
		foo = self.dir.add(('base', 'foo', 'foo', 'foo'), 'foo')

		self.assertEqual(foo, 'foo')
		self.assertFalse(self.dir.empty)
		self.assertIs(self.dir.get(('base',)), None)
		self.assertIs(self.dir.get(('base', 'foo')), None)
		self.assertIs(self.dir.get(('base', 'foo', 'foo')), None)
		self.assertIs(self.dir.get(('base', 'foo', 'foo', 'foo')), foo)


class Collection(unittest.TestCase):
	'''
		TargetDir features are very similiar to a collection for a nice
		interface lets assert a few more requirements of the collection protocol.
	'''

	def setUp(self):
		self.dir = TargetDir()

	def test_empty_keys(self):
		self.assertEqual(list(self.dir.keys()), [])

	def test_empty_values(self):
		self.assertEqual(list(self.dir.values()), [])

	def test_empty_items(self):
		self.assertEqual(list(self.dir.items()), [])

	def test_one_key(self):
		self.dir.add(('foo', 'bar'), 'FOO')
		self.assertSetEqual(
			set(self.dir.keys()),
			{('foo', 'bar')}
		)

	def test_one_value(self):
		self.dir.add(('foo', 'bar'), 'FOO')
		self.assertSetEqual(
			set(self.dir.values()),
			{'FOO'}
		)

	def test_one_item(self):
		self.dir.add(('foo', 'bar'), 'FOO')
		self.assertSetEqual(
			set(self.dir.items()),
			{(('foo', 'bar'), 'FOO')}
		)

class Traverse(unittest.TestCase):
	def setUp(self):
		self.dir = TargetDir()

	def test_empty(self):
		t = traverse(self.dir)
		self.assertRaises(StopIteration, next, t)

	def test_simple(self):
		foo = self.dir.add(('foo',), 'foo')
		t = traverse(self.dir)
		self.assertEqual(next(t),
			(('foo',), foo))
		self.assertEqual(next(t),
			(('foo',), foo))

	def test_deep(self):
		foo = self.dir.add(('base', 'foo'), 'foo')
		bar = self.dir.add(('base' ,'foo', 'bar'), 'bar')
		baz = self.dir.add(('base', 'foo', 'bar', 'baz'), 'baz')

		t = traverse(self.dir)
		self.assertEqual(next(t),
			(('base',), None))
		self.assertEqual(next(t),
			(('base', 'foo'), foo))
		self.assertEqual(next(t),
			(('base', 'foo', 'bar'), bar))
		self.assertEqual(next(t),
			(('base', 'foo', 'bar', 'baz'), baz))
		self.assertEqual(next(t),
			(('base', 'foo', 'bar', 'baz'), baz))

	def test_wide(self):
		base = self.dir.add(('base',), 'base')
		foo = self.dir.add(('base', 'foo'), 'foo')
		bar = self.dir.add(('base', 'bar'), 'bar')
		baz = self.dir.add(('base', 'baz'), 'baz')

		t = traverse(self.dir)
		path, target = next(t)
		self.assertEqual(target, base)

		visited = set()
		for (path, target) in t:
			visited.add(target)
			self.dir.remove(path)
		self.assertSetEqual(
			visited,
			{foo, bar, baz, base}
		)

class Removal(unittest.TestCase):
	def setUp(self):
		self.dir = TargetDir()
		self.dir.add(('base',), 'base')
		self.dir.add(('base', 'foo'), 'foo')
		self.dir.add(('inter', 'mediate', 'bar'), 'bar')
		self.dir.add(('inter', 'mediate', 'baz'), 'baz')
		self.dir.add(('inter', 'mediate', 'baz', 'zz'), 'zz')

	def test_simple(self):
		self.dir.remove(('base', 'foo'))
		self.assertRaises(KeyError, self.dir.get, ('base', 'foo'))

	def test_remove_non_existant(self):
		self.assertRaises(Exception, self.dir.remove, ('bar'))

	def test_remove_base(self):
		self.assertRaises(Exception, self.dir.remove, ('base'))

	def test_remove_intermediate(self):
		self.assertRaises(Exception, self.dir.remove, ('inter', 'mediate'))

	def test_remove_base_and_children(self):
		self.dir.remove(('base', 'foo'))
		self.dir.remove(('base',))

		self.assertRaises(KeyError, self.dir.get, ('base',))
		self.assertRaises(KeyError, self.dir.get, ('base', 'foo'))

	def test_remove_intermediate_and_children(self):
		self.dir.remove(('inter', 'mediate', 'bar'))
		self.dir.remove(('inter', 'mediate', 'baz', 'zz'))
		self.dir.remove(('inter', 'mediate', 'baz'))

		self.assertRaises(
			KeyError, self.dir.get, ('inter', 'mediate', 'bar')
		)
		self.assertRaises(
			KeyError, self.dir.get, ('inter', 'mediate', 'baz')
		)
		self.assertRaises(
			KeyError, self.dir.get, ('inter', 'mediate', 'baz', 'zz')
		)
		self.assertIs(self.dir.get(('inter', 'mediate')), None)  # really?

class Children(unittest.TestCase):
	def setUp(self):
		self.dir = TargetDir()

	def test_basic(self):
		foo = self.dir.add(('base', 'foo'), 'foo')
		bar = self.dir.add(('base', 'bar'), 'bar')

		c = set(self.dir.children(('base',)))
		self.assertSetEqual({
			(('base', 'foo'), foo),
			(('base', 'bar'), bar)
		}, c)

	def test_no_children(self):
		self.dir.add(('base', 'foo'), 'foo')
		self.dir.add(('base', 'bar'), 'bar')

		c = list(self.dir.children(('base', 'foo')))
		self.assertEqual(c, [])

	def test_level(self):
		self.dir.add(('base', 'foo'), 'foo')
		self.dir.add(('base', 'bar'), 'bar')
		self.dir.add(('test',), 'test')

		c = list(self.dir.children(('test',)))
		self.assertEqual(c, [])

	def test_level_with_children(self):
		self.dir.add(('base', 'foo'), 'foo')
		self.dir.add(('base', 'bar'), 'bar')
		self.dir.add(('test',), 'test')
		tfoo = self.dir.add(('test', 'foo'), 'tfoo')

		c = set(self.dir.children(('test',)))
		self.assertEqual({
			(('test', 'foo'), tfoo),
		}, c)

	def test_invalid(self):
		self.dir.add(('base', 'foo'), 'foo')
		self.dir.add(('base', 'bar'), 'bar')

		self.assertRaises(KeyError, list, self.dir.children(('test',)))
