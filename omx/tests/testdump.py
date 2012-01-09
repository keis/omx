#!/usr/bin/env python2

import unittest
from StringIO import StringIO

from .. import OMX, Template


class Dump(unittest.TestCase):
	def test_attributes(self):
		expected = '<foo id="buba"/>'
		data = ('buba',)
		foot = Template('foo', ('@id',),
			serialiser=lambda obj: ((obj[0],), {}))

		omx = OMX((foot,), 'foo')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue(), expected)

	def test_deep(self):
		expected = '<rec><rec><rec><rec><rec><rec/></rec></rec></rec></rec></rec>'
		data = 5

		rect = Template('rec', ('rec',))

		@rect.serialiser
		def rect(obj):
			if obj > 0:
				return ([obj - 1],), {}
			return ([],), {}

		omx = OMX((rect,), 'rec')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue(), expected)

	def test_intermediate(self):
		expected = '<root><persons><person name="foo"/><person name="bar"/></persons></root>'
		data = ('root', ['foo', 'bar'])

		roott = Template('root', (), {'persons/person/@name': 'names'},
			lambda names=None: ('root', names),
			lambda obj: ((), {'names': obj[1]}))

		omx = OMX((roott,), 'root')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue(), expected)

	def test_intermediate_root(self):
		expected = '''<root><items><item key="foo">fooz</item><item key="bar">barz</item></items></root>'''
		itemtt = Template('item', ('@key', 'text()'), {},
			lambda key, value: (key, ''.join(value)),
			lambda obj: (obj, {})
		)
		omx = OMX((itemtt,), 'root/items/item')
		result = omx.dump([('foo', 'fooz',), ('bar', 'barz')])
		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue(), expected)

if __name__ == '__main__':
	unittest.main()
