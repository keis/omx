from .core import TemplateHint
import decl

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
			serialiser=lambda obj: ((), {}),
			references=None
	):
		self.match = match
		self._factory = factory
		self._serialiser = serialiser
		# Store as sequence of key,value pairs to maintain order of ptargets
		self.targets = [(decl.target(k, references),v)
			for k,v in (ktargets or {}).items()]
		self.targets += [(decl.target(p, references), None)
			for p in (ptargets or [])]

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


class Namespace(object):
	def __init__(self, url, **references):
		self.url = url
		self.references = references
		self.references[''] = self.url
		self._templates = {}
		self.__prefix = '{%s}' % self.url if len(self.url) > 0 else ''

	def get_template(self, path):
		return self._templates[path[-1]]

	def add_template(self, template):
		self._templates[self.__prefix + template.match] = template

	def template(self, name, ptargets=None, ktargets=None):
		def decorator(func):
			tmpl = Template(
				name, ptargets, ktargets, func,
				references=self.references
			)
			self.add_template(tmpl)
			return tmpl
		return decorator


template = Namespace('').template
