from .core import TemplateHint

## TODO
# Make Template a type
# Instances of Template holds a object, this implies object is to be
#     serialised/unserialised with the template
#     (replaces current TemplateHint)
# Make it inheritable

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

	def __call__(self, obj):
		return TemplateHint(self, obj)

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
