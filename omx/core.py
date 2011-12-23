# vim: noet:ts=4:sw=4:

import itertools

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


class TargetDir(object):
	def __init__(self):
		self.__targets = {}

	def path(cls, pstr):
		if isinstance(pstr, basestring):
			return pstr.strip(' /').split('/')
		return pstr

	def get(self, path):
		path = self.path(path)
		current = self.__targets
		target = None
		for p in path:
			(current, target) = current[p]
		return target

	def __insert(self, path, target):
		current = self.__targets
		old = None
		for p in path:
			parent = current
			try:
				(current, old) = current[p]
			except KeyError:
				tmp = ({}, None)
				current[p] = tmp
				(current, old) = tmp
		if old is not None:
			raise Exception('Path already claimed by %r' % old)
		parent[p] = (current, target)

	def add(self, path, target):
		path = self.path(path)
		self.__insert(path, target)
		return target

	def remove(self, path):
		path = self.path(path)
		current = self.__targets
		for p in path:
			parent = current
			(current, target) = current[p]
		if len(current) > 0:
			raise Exception('sub-tree not empty')
		del parent[p]

	def emptytree(self, path):
		path = self.path(path)
		current = self.__targets
		for p in path:
			parent = current
			(current, target) = current[p]
		current.clear()

	def children(self, path):
		path = self.path(path)
		current = self.__targets
		for p in path:
			try:
				(current, target) = current[p]
			except KeyError:
				return
		for key, (g, child) in current.items():
			yield (tuple(path) + (key,), child)

	def __dfs(self, val, pre, ctx):
		for i, (child_ctx,t) in ctx.items():
			p = (pre + (i,))
			if t is not None:
				yield val(p, t)
			for x in self.__dfs(val, p, child_ctx):
				yield x

	def keys(self):
		return self.__dfs((lambda p, t: p), (), self.__targets)

	def values(self):
		return self.__dfs((lambda p, t: t), (), self.__targets)

	def items(self):
		return self.__dfs((lambda p, t: (p, t)), (), self.__targets)

	@property
	def empty(self):
		return len(self.__targets) == 0


def traverse(dir):
	path = ()
	while True:
		try:
			v = dir.get(path)
		except KeyError:
			path = path[:-1]
			continue
		children = dir.children(path)
		try:
			path, v = next(itertools.dropwhile(
				lambda x: x[0][-1].startswith('@'),
				children))
		except StopIteration:
			if v is None and path == ():
				return
		yield path, v


class OMXState(object):
	def __init__(self, omx):
		self.omx = omx
		self.path = []
		self.__targets = TargetDir()

	def add_target(self, path, name, singleton=None):
		''' Registers elements at 'path' relative the current path to be saved
			in new Target named 'name'. Returns the new Target instance.
		'''

		# combine path(s) with current path and detect if the path
		# should be marked as a singleton target
		paths = [self.__targets.path(p) for p in path.split('|')]
		indirect = any(len(p) > 1 for p in paths)
		if singleton is None:
			singleton = not indirect and \
				all(p[-1][0] == '@' or p[-1].endswith('()') for p in paths)
		paths = [tuple((self.path or []) + p) for p in paths]

		# Create handle
		target = Target(name, singleton)

		for path in paths:
			self.__targets.add(path, target)

		return target

	def has_target(self):
		return not self.__targets.empty

	def get_target(self, path=None):
		''' Get the Target instance registered for 'path' or the current path
			if None. Raises KeyError if no Target is registered for the path.
		'''

		if path is None:
			path = self.path

		return self.__targets.get(path)

	def remove_target(self, path=None):
		if path is None:
			path = self.path

		return self.__targets.remove(path)

	def prune_targets(self, path):
		''' Removes all targets registered for 'templatedata' '''
		self.__targets.emptytree(path)

	def itertargets(self):
		return traverse(self.__targets)

	def children(self, path=None):
		if path is None:
			path = self.path

		return self.__targets.children(path)

	def get_attributes(self, path=None):
		for ap, at in self.children(path):
			if ap[-1][0] == '@':
				v = at.pop()
				if at.empty:
					self.__targets.remove(ap)
				yield ap[-1][1:], v
