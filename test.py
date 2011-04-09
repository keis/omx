#!/usr/bin/env python2

import unittest
from StringIO import StringIO

from omx import OMX, Template

class OMXTest(unittest.TestCase):
	def setUp(self):
		self.data = StringIO(self.xmldata)

class Basic(OMXTest):
	xmldata = '<foo id="buba">Text<bar>one</bar>TEXT<bar>two</bar>text</foo>'

	def test_attibutes(self):
		foot = Template('foo', {'@id' : 'uid', 'bar' : 'bar'},
			lambda uid=None, bar=None: ('foo', uid))
		bart = Template('bar', {},
			lambda: None)
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, ('foo', 'buba'))

	def test_text(self):
		foot = Template('foo', {'bar' : 'bar'},
			lambda bar=None: bar)
		bart = Template('bar', {'text()' : 'text'},
			lambda text=None: ''.join(text))
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, ['one', 'two'])

	def test_tail_text(self):
		foot = Template('foo', {'text()' : 'text', 'bar' : 'bar'},
			lambda text=None, bar=None: ''.join(text))
		bart = Template('bar', {},
			lambda: None)
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, 'TextTEXTtext')

	def test_dict_factory(self):
		foot = Template('foo', {'@id' : 'uid', 'bar' : 'bar'},
			dict)
		bart = Template('bar', {},
			lambda: None)
		omx = OMX((foot,bart), 'foo')

		result = omx.load(self.data)

		self.assertEqual(result, {'uid' : 'buba', 'bar' : [None,None]})

class Feature(OMXTest):
	xmldata = '<root><items><item key="foo">fooz</item><item key="bar">barz</item></items></root>'

	def test_intermediate(self):
		roott = Template('root', {'items/item' : 'items'},
			lambda items=None: ('root', dict(items)))
		itemtt = Template('item', {'@key' : 'key', 'text()' : 'value'},
			lambda key=None,value=None: (key, ''.join(value)))
		omx = OMX((roott, itemtt), 'root')

		result = omx.load(self.data)
		self.assertEqual(result[0], 'root')
		self.assertEqual(result[1], {'foo' : 'fooz', 'bar' : 'barz'})

	def test_intermediate_attr(self):
		roott = Template('root', {'items/item/@key' : 'keys'},
			lambda keys=None: ('root', keys))
		omx = OMX((roott,) , 'root')

		result = omx.load(self.data)
		self.assertEqual(result[0], 'root')
		self.assertEqual(result[1], ['foo', 'bar'])

if __name__ == '__main__':
	unittest.main()
