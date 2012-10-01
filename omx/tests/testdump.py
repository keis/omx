#!/usr/bin/env python2

import unittest
try:
	from StringIO import StringIO
except ImportError:
	from io import BytesIO as StringIO

from .. import OMX, Template


class Dump(unittest.TestCase):
	def test_attributes(self):
		expected = '<foo id="buba"/>'
		data = ('buba',)
		foot = Template(
			'foo', ('@id',),
			serialiser=lambda dump, obj: dump(obj[0])
		)

		omx = OMX((foot,), 'foo')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue().decode('utf-8'), expected)

	def test_deep(self):
		expected = '<rec><rec><rec><rec><rec><rec/></rec></rec></rec></rec></rec>'
		data = 5

		rect = Template('rec', ('rec',))

		@rect.serialiser
		def rect(dump, obj):
			if obj > 0:
				dump([obj - 1])
			else:
				dump([])

		omx = OMX((rect,), 'rec')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue().decode('utf-8'), expected)

	def test_intermediate(self):
		expected = '<root><persons><person name="foo"/><person name="bar"/></persons></root>'
		data = ('root', ['foo', 'bar'])

		roott = Template(
			'root', (), {'persons/person/@name': 'names'},
			lambda names=None: ('root', names),
			lambda dump, obj: dump(names=obj[1])
		)

		omx = OMX((roott,), 'root')

		result = omx.dump(data)

		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue().decode('utf-8'), expected)

	def test_intermediate_root(self):
		expected = '''<root><items><item key="foo">fooz</item><item key="bar">barz</item></items></root>'''
		itemtt = Template(
			'item', ('@key', 'text()'), {},
			lambda key, value: (key, ''.join(value)),
			lambda dump, obj: dump(*obj)
		)
		omx = OMX((itemtt,), 'root/items/item')
		result = omx.dump([('foo', 'fooz',), ('bar', 'barz')])
		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue().decode('utf-8'), expected)

class Multitarget(unittest.TestCase):
	def test_multitarget(self):
		expected = '<root><foo/><bar/><foo/></root>';
		roott = Template('root', ('foo|bar',), {},
			lambda fb: fb,
			lambda dump, objs: dump(
				[foot(obj) if obj == 'foo' else bart(obj) for obj in objs]
			)
		)
		foot = Template('foo',
			factory=lambda: 'foo',
			serialiser=lambda dump, obj: dump()
		)
		bart = Template('bar',
			factory=lambda: 'bar',
			serialiser=lambda dump, obj: dump()
		)
		omx = OMX((roott, foot, bart), 'root')

		result = omx.dump(['foo', 'bar', 'foo'])
		out = StringIO()
		result.write(out)
		self.assertEqual(out.getvalue().decode('utf-8'), expected)

if __name__ == '__main__':
	unittest.main()
