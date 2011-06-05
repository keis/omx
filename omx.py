#!/usr/bin/env python2
# vim: noet:ts=4:sw=4:
''' Omx Maps Xml

	A module for mapping XML into python objects by rules defined by templates

	This module uses xpath like paths to designate elements in the tree, but
	supports far from all parts of the specification (thus xpath like). In
	addition to simple relative paths attributes may be access with @-symbol
	and the text of a node with text(), but no other xpath functions is supported.
'''

## TODO / Wishlist
# Refactor Target singleton checks (method(s) in Target?)
# Serialisation reusing the same templates
# XML schema from templates ( relax ng ? )
# Aliasing or Template inheritance
# Easy singleton targets from template decorator / object
## use [] syntax? like "/foo/bar[0]"
## or something regexp inspired *, +, {3}

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

		ptargets is sequence of paths
		ktargets is a dictionary mapping paths to names
		factory is a function or type that will be called with the data
			defined by ptargets as positional arguments and ktargets as
			keyword arguments.
	'''
	def __init__(self, match, ptargets=None, ktargets=None, factory=lambda: None):
		self.match = match
		self.factory = factory
		# Store as sequence of key,value pairs to maintain order of ptargets
		self.targets = (ktargets or {}).items()
		self.targets += [(p, None) for p in (ptargets or [])]


def template(name, ptargets=None, ktargets=None):
	def decorator(func):
		return Template(name, ptargets, ktargets, func)
	return decorator


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
			in template.targets]

	def create(self):
		''' Creates a new object by calling the factory of the Template with
			the values stored '''

		# Build positonal and keyword -arguments
		args = []
		kwargs = {}
		for t in self.values:
			if t.name is None:
				if t.singleton and t.data is None:
					raise Exception("Missing argument (arg %d to %s)" %
						(len(args) + 1, self.template.match))
				args.append(t.data)
			else:
				if t.data is not None or not t.singleton:
					kwargs[t.name] = t.data

		# Create object
		return self.template.factory(*args, **kwargs)


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
		root_target = state.add_target(self.root, 'root', ('/' not in self.root))

		for event, element in etree.iterparse(xmldata, events=('start', 'end')):
			if event == 'start':
				state.push(element)
			elif event == 'end':
				state.pop(element)
				element.clear()
			else:  # pragma: no cover
				assert False

		return root_target.data


class OMXState(object):
	def __init__(self, omx):
		self.omx = omx
		self.path = []
		self.elemtails = []
		self.targets = {}
		self.context = {'ids': {}}

	def add_target(self, path, name, singleton=None):
		''' Registers elements at 'path' relative the current path to be saved
			in new Target named 'name'. Returns the new Target instance.
		'''

		paths = [tuple(self.path + p.strip().split('/')) for p in path.split('|')]
		if singleton is None:
			singleton = len(paths) == 1 and (path[0] == '@' or path == 'text()')
		target = Target(name, singleton)

		# Currently only supports one target per element
		# May change if a proper usecase is found
		for path in paths:
			if path in self.targets and self.targets[path] is not None:
				raise Exception("Path already claimed (%s %s)" % (path, name))

		for path in paths:
			self.targets[path] = target

			# Add null targets for unclaimed intermediate steps
			for l in range(len(path), 0, -1):
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

		for k, v in self.targets.items():
			if v in templatedata.values:
				del self.targets[k]

	def push(self, element):
		''' Called when the parser descends into the tree, causing a new element
			to be pushed to the end of the path.

			Initialises a TemplateData instance for the element if needed and fills
			any attribute targets registered for the element

		'''

		self.path.append(element.tag)

		try:
			target = self.get_target()
		except KeyError:
			# An early exit branch should be added to push/pop for the case
			# when a subtree is not mapped to a object
			raise Exception("SKIP not implemented (element without target '%s')"
				% element.tag)

		# Push empty state to text collector
		self.elemtails.append([])

		if target is not None:
			# Create TemplateData instance to collect data of this element
			template = self.omx.get_template(self.path)
			data = TemplateData(template, self)
			if target.singleton:
				target.data = data
			else:
				target.data.append(data)
			if 'id' in element.attrib:
				self.context['ids'][element.attrib['id']] = data

		# Fill attribute targets
		for k, v in element.attrib.items():
			try:
				target = self.get_target(self.path + ['@%s' % k])
				if target.singleton:
					target.data = v
				else:
					target.data.append(v)
			except KeyError:
				pass

	def pop(self, element):
		''' Called when the parser ascends the tree, causing the last element
			of the path to be popped.

			Fills text() and context() targets
			Replaces target TemplateData with destination object instance.
		'''

		assert self.path[-1] == element.tag

		# Pop text collector state and add the text tail of element
		tails = self.elemtails.pop()
		if len(self.elemtails) > 0:
			self.elemtails[-1].append(element.tail or '')

		# Fill text target: text of current element + tail of all child elements
		try:
			target = self.get_target(self.path + ['text()'])
			text = [element.text or ''] + tails
			if target.singleton:
				target.data = text
			else:
				target.data.append(text)
		except KeyError:
			pass

		# Fill context target
		try:
			target = self.get_target(self.path + ['context()'])
			target.data = self.context
		except KeyError:
			pass

		target = self.get_target()
		self.path.pop()
		if target is None:
			return

		# Create object from TemplateData and clean up
		if target.singleton:
			data = target.data
		else:
			data = target.data[-1]

		assert isinstance(data, TemplateData)
		self.prune_targets(data)

		obj = data.create()

		if target.singleton:
			target.data = obj
		else:
			target.data[-1] = obj

		# Save in ID dictionary if id is set
		if 'id' in element.attrib:
			self.context['ids'][element.attrib['id']] = obj


if __name__ == '__main__':  # pragma: no cover
	from StringIO import StringIO
	data = '''<root>
				<persons>
					<person name="foo"/>
					<person name="bar">bla bla</person>
				</persons>
			</root>'''

	roott = Template('root', (), {'persons/person/@name': 'names'},
		lambda names=None: ('root', names))
	omx = OMX((roott,), 'root')
	v = omx.load(StringIO(data))
	print v
