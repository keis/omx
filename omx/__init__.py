#!/usr/bin/env python2
# vim: noet:ts=4:sw=4:
''' Omx Maps Xml

	A module for mapping XML into python objects by rules defined by templates

	This module uses xpath like paths to designate elements in the tree, but
	supports far from all parts of the specification (thus xpath like). In
	addition to simple relative paths attributes may be access with @-symbol
	and the text of a node with text(), but no other xpath functions is
	supported.  '''

## TODO / Wishlist
# Refactor Target singleton checks (method(s) in Target?) Serialisation reusing
# the same templates XML schema from templates ( relax ng ? ) Aliasing or
# Template inheritance Easy singleton targets from template decorator / object
## use [] syntax? like "/foo/bar[0]" ## or something regexp inspired *, +, {3}

__all__ = ('OMX', 'template', 'Template')

from lxml import etree
from .core import template, Template

class OMX(object):
	''' Defines how a XML document is converted into objects '''

	def __init__(self, templates, root):
		self.templates = dict((t.match, t) for t in templates)
		self.root = root

	def get_template(self, path):
		''' Get the template used to map path into a object '''
		return self.templates[path[-1]]

	def load(self, xmldata):
		from .load import LoadState
		''' Maps 'xmldata' into objects as defined by the templates '''
		state = LoadState(self)
		root_target = state.add_target(self.root, 'root', ('/' not in self.root))

		for event, element in etree.iterparse(xmldata, events=('start', 'end')):
			if event == 'start':
				state.push(element)
			elif event == 'end':
				state.pop(element)
				element.clear()
			else:  # pragma: no cover
				assert False

		return root_target.get()

	def dump(self, obj):
		''' Maps 'obj' into a xml as defined by the templates '''
		from .dump import DumpState
		state = DumpState(self)
		state.add_target(self.root, 'root', ('/' not in self.root))

		stack = []
		for event, element in state.dump(obj):
			if event == 'start':
				if stack:
					stack[-1].append(element)
				else:
					tree = etree.ElementTree(element)
				stack.append(element)
			elif event == 'end':
				element = stack.pop()
			else:
				assert False

		return tree
