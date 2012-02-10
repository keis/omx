#!/usr/bin/env python2

import unittest
from StringIO import StringIO

from .. import OMX, Template, template, Namespace

class BasicLoad(unittest.TestCase):
	## Vocabulary
	foo = Namespace('http://dummy/foo'
	)
	@foo.template(
		'link',
		(),
		{
			'@self:description': 'desc',
			'@date': 'date'
		}
	)
	def foo_link(desc=None, date=None):
		return (
			'FOO' +
			('?' + desc if desc else '') +
			('?' + date if date else '')
		)

	bar = Namespace('http://dummy/bar')
	@bar.template('link', (), {'description': 'desc'})
	def bar_link(desc=None):
		return 'BAR' + (desc[0] if desc else '')

	@bar.template('description', ('text()',))
	def bar_desc(t):
		return '?' + ''.join(t)

	baz = Namespace('http://dummy/baz',
		bar='http://dummy/bar'
	)
	@baz.template('collection', ('bar:link',))
	def baz_collection(blinks):
		return ('baz', blinks)

	## TESTS
	def test_alias(self):
		'''
			Test loading a simple structure with two different references to
			the same namespace
		'''

		rootns = Namespace('',
			f='http://dummy/foo',
		)

		@rootns.template('root', ('f:link',))
		def root(flinks):
			return flinks

		xmldata = '<root><foo:link xmlns:foo="http://dummy/foo"/><alias:link xmlns:alias="http://dummy/foo"/></root>'
		omx = OMX((self.foo, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, ['FOO', 'FOO'])

	def test_load_nested(self):
		'''
			Test loading a structure where a template has a reference to
			another element in the same namespace
		'''

		rootns = Namespace('',
			b='http://dummy/bar',
		)
		
		@rootns.template('root', ('b:link',))
		def root(blinks):
			return blinks

		xmldata = '<root xmlns:bar="http://dummy/bar"><bar:link><bar:description>D</bar:description></bar:link><bar:link/></root>'
		omx = OMX((self.bar, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, ['BAR?D', 'BAR'])

	def test_load_parallel(self):
		'''
			Test loading a structure with two elements of the same name but of
			different namespace
		'''

		rootns = Namespace('',
			f='http://dummy/foo',
			b='http://dummy/bar'
		)

		@rootns.template('root', ('f:link','b:link'))
		def root(flinks, blinks):
			return flinks, blinks

		xmldata = '<root><foo:link xmlns:foo="http://dummy/foo"/><bar:link xmlns:bar="http://dummy/bar"/></root>'
		omx = OMX((self.foo, self.bar, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, (['FOO'], ['BAR']))

	def test_load_cross(self):
		'''
			Test loading with a template that has a reference to a element from
			another namespace
		'''

		rootns = Namespace('',
			z='http://dummy/baz'
		)

		@rootns.template('root', ('z:collection',))
		def root(zc):
			return zc

		xmldata = '<root xmlns:zz="http://dummy/baz" xmlns:b="http://dummy/bar"><zz:collection><b:link/></zz:collection></root>'
		omx = OMX((self.baz, self.bar, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, [('baz', ['BAR'])])

	def test_load_defaultns(self):
		'''
			Test loading with default namespace set
		'''
		rootns = Namespace('',
			b='http://dummy/bar'
		)

		@rootns.template('root', ('b:link',))
		def root(blinks):
			return blinks

		xmldata = '<root><link xmlns="http://dummy/bar"><description>desc</description></link></root>'
		omx = OMX((self.bar, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, ['BAR?desc'])

	def test_nsroot(self):
		rootns = Namespace(
			'http://dummy/root',
		)

		@rootns.template('root')
		def root():
			return 'ROOT'

		xmldata = '<root xmlns="http://dummy/root"></root>'
		omx = OMX((rootns,), '{http://dummy/root}root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, 'ROOT')

	def test_nsattribute(self):
		rootns = Namespace(
			'',
			f='http://dummy/foo'
		)

		@rootns.template('root', ('f:link',))
		def root(flinks):
			return flinks

		xmldata = '<root><foo:link xmlns:foo="http://dummy/foo" foo:description="desc"/></root>'
		omx = OMX((self.foo, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, ['FOO?desc'])

	def test_nsattribute_default(self):
		'''
			The default namespace does *not* apply to attributes
		'''

		rootns = Namespace(
			'',
			f='http://dummy/foo'
		)

		@rootns.template('root', ('f:link',))
		def root(flinks):
			return flinks

		xmldata = '<root><link xmlns="http://dummy/foo" date="now"/></root>'
		omx = OMX((self.foo, root), 'root')

		result = omx.load(StringIO(xmldata))
		self.assertEquals(result, ['FOO?now'])
