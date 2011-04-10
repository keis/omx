#!/usr/bin/env python2

import unittest
from StringIO import StringIO

from omx import OMX, Template, template

class OMXTest(unittest.TestCase):
	def setUp(self):
		self.data = StringIO(self.xmldata)

class Basic(OMXTest):
	xmldata = '<foo id="buba">Text<bar>one</bar>TEXT<bar>two</bar>text</foo>'

	def test_attibutes(self):
		foot = Template('foo', ('@id', 'bar'), 
			factory=lambda uid, bar: ('foo', uid))
		bart = Template('bar')
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, ('foo', 'buba'))

	def test_text(self):
		foot = Template('foo', ('bar',), {},
			lambda bar=None: bar)
		bart = Template('bar', (), {'text()' : 'text'},
			lambda text=None: ''.join(text))
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, ['one', 'two'])

	def test_tail_text(self):
		foot = Template('foo', ('text()', 'bar'), {},
			lambda text, bar: ''.join(text))
		bart = Template('bar')
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, 'TextTEXTtext')

	def test_dict_factory(self):
		foot = Template('foo', (), {'@id' : 'uid', 'bar' : 'bar'},
			dict)
		bart = Template('bar')
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, {'uid' : 'buba', 'bar' : [None,None]})

class Intermediate(OMXTest):
	xmldata = '<root><items><item key="foo">fooz</item><item key="bar">barz</item></items></root>'

	def test_intermediate(self):
		roott = Template('root', ('items/item',), {},
			lambda items: ('root', dict(items)))
		itemtt = Template('item', ('@key', 'text()'), {},
			lambda key,value: (key, ''.join(value)))
		omx = OMX((roott, itemtt), 'root')

		result = omx.load(self.data)
		self.assertEqual(result[0], 'root')
		self.assertEqual(result[1], {'foo' : 'fooz', 'bar' : 'barz'})

	def test_intermediate_attr(self):
		roott = Template('root', ('items/item/@key',), {},
			lambda keys: ('root', keys))
		omx = OMX((roott,) , 'root')

		result = omx.load(self.data)
		self.assertEqual(result[0], 'root')
		self.assertEqual(result[1], ['foo', 'bar'])

class Multitarget(OMXTest):
	xmldata = '<root><foo>hello</foo><bar>world</bar><foo>!</foo></root>'

	def test_multitarget(self):
		roott = Template('root', ('foo|bar',), {},
			lambda fb: fb)
		foot = Template('foo',
			factory = lambda: 'foo')
		bart = Template('bar',
			factory = lambda: 'bar')
		omx = OMX((roott, foot, bart), 'root')

		result = omx.load(self.data)
		self.assertEqual(result, ['foo', 'bar', 'foo'])

	def test_multitarget_text(self):
		roott = Template('root', ('foo|bar',), {},
			lambda fb: ' '.join(fb))
		foot = Template('foo', (), {'text()' : 'text'},
			lambda text=None: ''.join(text))
		bart = Template('bar', (), {'text()' : 'text'},
			lambda text=None: ''.join(text))
		omx = OMX((roott, foot, bart), 'root')

		result = omx.load(self.data)
		self.assertEqual(result, "hello world !")

	def test_multitarget_text_s(self):
		@template('root', ('foo/text()|bar/text()',))
		def roott(fb):
			r = []
			map(r.extend, fb)
			return r
		omx = OMX((roott,), 'root')

		result = omx.load(self.data)
		self.assertEqual(result, ["hello", "world", "!"])

class Context(OMXTest):
	xmldata = '<root><foo id="FOO">test</foo><bar id="BAR"/></root>'

	def test_context(self):
		@template('root', ('foo', 'bar'))
		def roott(foo, bar):
			return bar

		@template('foo', ('context()', 'text()'))
		def foot(context, text):
			context.update({'grisapa' : ''.join(text)})

		@template('bar', ('context()',))
		def bart(context):
			return context['grisapa'].upper()

		omx = OMX((roott, foot, bart), 'root')

		result = omx.load(self.data)
		self.assertEqual(result, ['TEST'])

	def test_ids(self):
		roott = Template('root', ('foo', 'bar', 'context()'), {},
			lambda foo, bar, context: context['ids'].keys())
		foot = Template('foo', (), {},
			lambda: 'foo')
		bart = Template('bar', (), {},
			lambda: 'bar')
		omx = OMX((roott, foot, bart), 'root')

		result = omx.load(self.data)
		self.assertEqual(result, ['FOO', 'BAR'])

if __name__ == '__main__':
	unittest.main()
