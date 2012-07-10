#!/usr/bin/env python2

import unittest
from StringIO import StringIO

from .. import OMX, Template, template

class OMXTest(unittest.TestCase):
	def setUp(self):
		self.data = StringIO(self.xmldata)

class CrissCross(OMXTest):
	xmldata = '<root><foo><i>1</i><s>one</s></foo><foo><i>2</i><s>two</s></foo></root>'

	def test_basic(self):
		@template('root', ('foo/i/text()', 'foo/s/text()'))
		def roott(fi, fs):
			return {
				'int': [int(''.join(i)) for i in fi],
				'string': [''.join(s) for s in fs]
			}

		omx = OMX((roott,), 'root')
		result = omx.load(self.data)

		self.assertEqual(result, {'int': [1,2], 'string': ['one', 'two']})
