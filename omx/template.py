from .core import TemplateHint
from . import decl

## TODO
# Make Template a type
# Instances of Template holds a object, this implies object is to be
#     serialised/unserialised with the template
#     (replaces current TemplateHint)
# Make it inheritable

class Template(object):
    '''
        Defines how elements matched by `match` is converted to objects
    '''

    def __init__(self, match, ptargets=None, ktargets=None,
            factory=lambda: None,
            serialiser=lambda values, obj: values(obj),
            nsmap=None
    ):
        '''
            `match` the tag this template maps

            `ptargets` a sequence of paths

            `ktargets` a dictionary mapping paths to names

            `factory` a function or type that will be called with the data
                defined by `ptargets` as positional arguments and `ktargets` as
                keyword arguments to create the object.

            `serialiser` a function that will be called with a callback and the
                object being serialised that should provide the data to save

            `nsmap` a dictionary with namespaces and the names they are
                referenced by in the path strings in `ptargets` and `ktargets`
        '''

        self.match = match
        self._factory = factory
        self._serialiser = serialiser
        # Store as sequence of key,value pairs to maintain order of ptargets
        self.targets = [(decl.target(k, nsmap),v)
            for k,v in (ktargets or {}).items()]
        self.targets += [(decl.target(p, nsmap), None)
            for p in (ptargets or [])]

    def __call__(self, obj):
        ''' hint that `obj` should be serialised using this template '''
        return TemplateHint(self, obj)

    def __repr__(self):
        return '<Template matching "%s">' % (self.match,)

    def factory(self, fun):
        ''' Use `fun` as the factory, to be used as decorator '''
        self._factory = fun
        return self

    def serialiser(self, fun):
        ''' use `fun` as the serialiser, to be used as a decorator '''
        self._serialiser = fun
        return self


class Namespace(object):
    '''
        Used to define a namespace

        A namespace is a collection of templates associated with a
        XML namespace identified by `url`

        This class contain methods for getting templates in the namespace and
        defining the templates of the namespace
    '''

    def __init__(self, url, nsmap=None):
        '''
            `url` the url of XML namespace
            
            `nsmap` a dictionary with namespaces and the names, the names
                can be used when defining templates in this namespace
        '''

        self.url = url
        self.nsmap = nsmap or {}
        self.nsmap[''] = self.nsmap['self'] = self.url
        self._templates = {}
        self.__prefix = '{%s}' % self.url if len(self.url) > 0 else ''

    def get_template(self, path):
        return self._templates[path[-1]]

    def add_template(self, template):
        self._templates[self.__prefix + template.match] = template

    def template(self, name, ptargets=None, ktargets=None):
        '''
            Get a decorator that defines a `Template` using `name`, `ktargets'
            and `ktargets`. see `Template` for information on the meaning of
            these argumets
        '''
        def decorator(func):
            tmpl = Template(
                name, ptargets, ktargets, func,
                nsmap=self.nsmap
            )
            self.add_template(tmpl)
            return tmpl
        return decorator


# define a free template decorator for easy use of namespace unaware loaders
template = Namespace('').template
