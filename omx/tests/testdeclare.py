#!/usr/bin/env python2

import unittest
from ..decl import path, target


class PathString(unittest.TestCase):
	def test_tagname(self):
		self.assertEquals(
			path('foo'),
			['foo']
		)

	def test_split(self):
		self.assertEquals(
			path('foo/bar'),
			['foo', 'bar']
		)

	def test_split_trailing(self):
		self.assertEquals(
			path('foo/bar/'),
			['foo', 'bar']
		)

	def test_attribute(self):
		self.assertEquals(
			path('@boo'),
			['@boo']
		)


class NsPathString(unittest.TestCase):
	def test_default(self):
		self.assertEquals(
			path('foo', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['{http://default}foo']
		)

	def test_default_split(self):
		self.assertEquals(
			path('foo/bar', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['{http://default}foo', '{http://default}bar']
		)

	def test_default_attrib(self):
		self.assertEquals(
			path('@boo', references={
				'': 'http://test'
			}),
			['@boo']
		)

	def test_explicit(self):
		self.assertEquals(
			path('x:foo', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['{http://test}foo']
		)

	def test_explicit_split(self):
		self.assertEquals(
			path('x:foo/bar', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['{http://test}foo', '{http://default}bar']
		)

	def test_explicit_attrib(self):
		self.assertEquals(
			path('@x:boo', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['@{http://test}boo']
		)

	def test_explicit_nons(self):
		self.assertEquals(
			path(':boo', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['boo']
		)

	def test_explicit_nons_attrib(self):
		self.assertEquals(
			path('@:boo', references={
				'': 'http://default',
				'x': 'http://test'
			}),
			['@boo']
		)
