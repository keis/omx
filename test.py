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


if __name__ == '__main__':
	unittest.main()
