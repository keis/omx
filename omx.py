#!/usr/bin/env python2
''' OMX - Omx Maps Xml

	A module for mapping XML into python objects by rules defined by templates

	This module uses xpath like paths to designate elements in the tree, but
	supports far from all parts of the specification (thus xpath like). In
	addition to simple relative paths attributes may be access with @ and the 
	text of a node with text(), but no other xpath functions is supported.
'''

from lxml import etree

class Target(object):
	''' Holds the data passed to a factory as 'name'

		In general 'data' will be a list of objects created from other templates,
		but may be string when mapped to a attribute or text()

		During load the last item may be an instance of TemplateData.
	'''
	## TODO
	# check the invariants when setting data

	def __init__(self, name, singleton):
		self.name = name
		self.singleton = singleton
		self.data = None if singleton else []


class Template(object):
	''' Defines how elements matched by 'match' is converted to objects

		targets is a dictionary mapping paths to names
		factory is a function or type that will be called with the data
			defined by targets as keyword arguments
	'''
	def __init__(self, match, targets, factory):
		self.match = match
		self.targets = targets
		self.factory = factory


class TemplateData(object):
	''' Collects the data need to create a object as defined by 'template'
		When created registers targets for sub-objects with the OMXState.

		template is the template that data is collected for
		values is a list of Target instances for all sub-objects
	'''
	## TODO
	# add method to verify values are of the proper type ?

	def __init__(self, template, state):
		self.template = template
		self.values = [state.add_target(path, name) for (path, name)
			in template.targets.items()]


class OMX(object):
	''' Defines how a XML document is converted into objects '''

	def __init__(self, templates, root):
		self.templates = dict((t.match, t) for t in templates)
		self.root = root


	def get_template(self, path):
		''' Get the template used to map path into a object '''
		return self.templates[path[-1]]


	def load(self, xmldata):
		''' Maps 'xmldata' into objects as defined by the templates '''
		state = OMXState(self)
		root_target = state.add_target(self.root, 'root')

		for event,element in etree.iterparse(xmldata, events = ('start', 'end')):
			if event == 'start':
				state.push(element)
			elif event == 'end':
				state.pop(element)
			else:
				assert False

		return root_target.data[0]


class OMXState(object):
	def __init__(self, omx):
		self.omx = omx
		self.path = []
		self.targets = {}


	def add_target(self, path, name):
		''' Registers elements at 'path' relative the current path to be saved
			in new Target named 'name'. Returns the new Target instance.
		'''

		singleton = path[0] == '@' or path == 'text()'
		path = tuple(self.path + path.split('/'))
		target = Target(name, singleton)

		# Currently only supports one target per element
		# May change if a proper usecase is found
		if path in self.targets and self.targets[path] is not None:
			raise Exception("Path already claimed (%s %s)", (path, name))

		self.targets[path] = target

		# Add null targets for unclaimed intermediate steps
		for l in range(len(path),0,-1):
			if path[:l] not in self.targets:
				self.targets[path[:l]] = None

		return target


	def get_target(self, path=None):
		''' Get the Target instance registered for 'path' or the current path
			if None. Raises KeyError if no Target is registered for the path.
		'''

		if path is None:
			path = self.path

		if isinstance(path, str):
			path = path.split('/')

		return self.targets[tuple(path)]


	def prune_targets(self, templatedata):
		''' Removes all targets registered for 'templatedata' '''

		for k,v in self.targets.items():
			if v in templatedata.values:
				del self.targets[k]


	def push(self, element):
		try:
			target = self.get_target(self.path + [element.tag])
		except KeyError:
			# An early exit branch should be added to push/pop for the case
			# when a subtree is not mapped to a object
			raise Exception('SKIP not implemented')

		self.path.append(element.tag)

		if target is not None:
			# Create TemplateData instance to collect data of this element
			template = self.omx.get_template(self.path)
			target.data.append(TemplateData(template, self))

		# Fill attribute targets
		for k,v in element.attrib.items():
			try:
				target = self.get_target(self.path + ['@%s' % k])
				if target.singleton:
					target.data = v
				else:
					target.data.append(v)
			except KeyError:
				pass


	def pop(self, element):
		assert self.path[-1] == element.tag

		try:
			target = self.get_target(self.path + ['text()'])
			if target.singleton:
				target.data = element.text
			else:
				target.data.append(element.text)
		except KeyError:
			pass

		target = self.get_target()

		self.path.pop()

		if target is None:
			return

		assert isinstance(target.data[-1], TemplateData)
		self.prune_targets(target.data[-1])

		values = dict([(t.name, t.data) for t in target.data[-1].values])
		target.data[-1] = target.data[-1].template.factory(**values)


if __name__ == '__main__':
	from StringIO import StringIO

	roott = Template('root', {'persons/person/@name' : 'names'},
		lambda names=None: ('root', names))
	omx = OMX((roott,), 'root')
	v = omx.load(StringIO('<root><persons><person name="foo"/><person name="bar">bla bla</person></persons></root>'))
	print v
