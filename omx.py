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
		self._data = None if singleton else []


	def __repr__(self):
		return '<Target %s (%s)>' % (self.name, len(self))

	def __len__(self):
		if self.singleton:
			return 0 if self._data is None else 1
		return len(self._data)

	@property
	def empty(self):
		if self.singleton:
			return self._data is None
		return len(self._data) == 0

	@property
	def value(self):
		if self.singleton:
			if self._data is None:
				raise IndexError("No value set")
			return self._data
		return self._data[-1]

	@value.setter
	def value(self, val):
		if self.singleton:
			self._data = val
		else:
			self._data[-1] = val

	def add(self, value):
		if self.singleton:
			if self._data is not None:
				raise Exception("Value already set for singleton target")
			self._data = value
		else:
			self._data.append(value)

	def pop(self):
		if self.singleton:
			if self._data is None:
				raise IndexError("No value set")
			value = self._data
			self._data = None
		else:
			value = self._data.pop()

		return value

	def get(self):
		return self._data

	def set(self, d):
		if not self.singleton:
			d = list(d)
		self._data = d


class Template(object):
	''' Defines how elements matched by 'match' is converted to objects

		ptargets is sequence of paths
		ktargets is a dictionary mapping paths to names
		factory is a function or type that will be called with the data
			defined by ptargets as positional arguments and ktargets as
			keyword arguments.
	'''
	def __init__(self, match, ptargets=None, ktargets=None,
			factory=lambda: None,
			serialiser=lambda obj: ((), {})):
		self.match = match
		self._factory = factory
		self._serialiser = serialiser
		# Store as sequence of key,value pairs to maintain order of ptargets
		self.targets = (ktargets or {}).items()
		self.targets += [(p, None) for p in (ptargets or [])]

	def __repr__(self):
		return '<Template matching "%s">' % (self.match,)

	def factory(self, fun):
		self._factory = fun
		return self

	def serialiser(self, fun):
		self._serialiser = fun
		return self


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
		add = state.add_target
		self.values = [add(path, name) for (path, name) in template.targets]

	def __repr__(self):
		return '<TemplateData of %r>' % self.template

	def create(self):
		''' Creates a new object by calling the factory of the Template with
			the values stored '''

		# Build positonal and keyword -arguments
		args = []
		kwargs = {}
		for t in self.values:
			if t.name is None:
				if t.singleton and t.empty:
					raise Exception("Missing argument (arg %d to %s)" %
						(len(args) + 1, self.template.match))
				args.append(t.get())
			else:
				if not t.empty or not t.singleton:
					kwargs[t.name] = t.get()

		# Create object
		return self.template._factory(*args, **kwargs)

	def dump(self, obj):
		(args, kwargs) = self.template._serialiser(obj)
		args = list(args)
		args.reverse()
		for t in self.values:
			if t.name is None:
				t.set(args.pop())
			else:
				t.set(kwargs[t.name])


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

class OMXState(object):
	def __init__(self, omx):
		self.omx = omx
		self.path = []
		self.__targets = {}

	def add_target(self, path, name, singleton=None):
		''' Registers elements at 'path' relative the current path to be saved
			in new Target named 'name'. Returns the new Target instance.
		'''

		# combine path(s) with current path and detect if the path
		# should be marked as a singleton target
		paths = [p.strip(' /').split('/') for p in path.split('|')]
		indirect = any(len(p) > 1 for p in paths)
		if singleton is None:
			singleton = not indirect and \
				all(p[-1][0] == '@' or p[-1].endswith('()') for p in paths)
		paths = [tuple((self.path or []) + p) for p in paths]

		# Create handle
		target = Target(name, singleton)

		# Currently only supports one target per element
		# May change if a proper usecase is found
		for path in paths:
			if path in self.__targets and self.__targets[path] is not None:
				raise Exception("Path already claimed (%s %s)" % (path, name))

		for path in paths:
			self.__targets[path] = target

			# Add null targets for unclaimed intermediate steps
			for l in range(len(path), 0, -1):
				if path[:l] not in self.__targets:
					self.__targets[path[:l]] = None

		return target

	def has_target(self):
		return len(self.__targets) > 0

	def get_target(self, path=None):
		''' Get the Target instance registered for 'path' or the current path
			if None. Raises KeyError if no Target is registered for the path.
		'''

		if path is None:
			path = self.path

		if isinstance(path, str):
			path = path.strip(' /').split('/')

		return self.__targets[tuple(path)]

	def remove_target(self, path=None):
		if path is None:
			path = self.path

		if isinstance(path, str):
			path = path.strip(' /').split('/')

		del self.__targets[tuple(path)]

	def prune_targets(self, templatedata):
		''' Removes all targets registered for 'templatedata' '''

		for k, v in self.__targets.items():
			if v in templatedata.values:
				self.remove_target(k)

	def next_target(self, path=None):
		if path is None:
			path = self.path

		if isinstance(path, str):
			path = path.strip(' /').split('/')

		tpaths = [p for p in self.__targets.keys() if not p[-1][0].startswith('@')]
		tpaths.sort()

		if len(path) == 0:
			path = tpaths[0]
			return path, self.__targets[path]
		i = tpaths.index(tuple(path))

		if len(tpaths) > i + 1 and (path is None or tpaths[i + 1][-2] == path[-1]):
			target = self.__targets[tpaths[i + 1]]
			return tpaths[i + 1], target
		else:
			target = self.__targets[tpaths[i]]
			return tpaths[i], target

	def children(self, path):
		if isinstance(path, str):
			path = path.strip(' /').split('/')

		pl = len(path)
		for ap, at in self.__targets.items():
			if len(ap) == pl + 1 and ap[-2] == path[-1]:
				yield ap, at

	def get_attributes(self, path):
		for ap, at in self.children(path):
			if ap[-1][0] == '@':
				v = at.pop()
				if at.empty:
					del self.__targets[ap]
				yield ap[-1][1:], v


class DumpState(OMXState):
	def __init__(self, omx):
		OMXState.__init__(self, omx)

	def dump(self, obj):
		self.next_target()[1].add(obj)

		while self.has_target():
			path, target = self.next_target()
			lpath = list(path)
			repeat = lpath == self.path
			self.path = lpath

			# this could be refactored by merging the two main branches
			if target is None:
				if repeat:
					yield 'end', None

				attributes = dict(self.get_attributes(path))
				if attributes or list(self.children(path)):
					element = etree.Element(path[-1])
					element.attrib.update(attributes)
					yield 'start', element
				else:
					self.remove_target(path)
					self.path.pop()

			else:
				if repeat:
					assert isinstance(target.value, TemplateData)
					yield 'end', None
					target.pop()

				if target.empty:
					self.remove_target(path)
					self.path.pop()
					continue

				# Set up new template data
				template = self.omx.get_template(path)
				data = TemplateData(template, self)
				data.dump(target.value)
				target.value = data

				# Create element
				element = etree.Element(data.template.match)
				attributes = dict(self.get_attributes(path))
				element.attrib.update(attributes)
				yield 'start', element


class LoadState(OMXState):
	def __init__(self, omx):
		OMXState.__init__(self, omx)
		self.elemtails = []
		self.context = {'ids': {}}

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
			target.add(data)
			if 'id' in element.attrib:
				self.context['ids'][element.attrib['id']] = data

		# Fill attribute targets
		for k, v in element.attrib.items():
			try:
				target = self.get_target(self.path + ['@%s' % k])
				target.add(v)
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
			target.add(text)
		except KeyError:
			pass

		# Fill context target
		try:
			target = self.get_target(self.path + ['context()'])
			target.add(self.context)
		except KeyError:
			pass

		target = self.get_target()
		self.path.pop()
		if target is None:
			return

		# Create object from TemplateData and clean up
		data = target.value

		assert isinstance(data, TemplateData)
		self.prune_targets(data)

		obj = data.create()

		target.value = obj

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
		lambda names=None: ('root', names),
		lambda obj: ((), {'names': obj[1]}))
	omx = OMX((roott,), 'root')
	v = omx.load(StringIO(data))
	print v

	s = omx.dump(v)
	out = StringIO()
	s.write(out)
	print out.getvalue()
