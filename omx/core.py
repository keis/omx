# vim: ts=4:sw=4:

import itertools
from .target import Target


class TemplateHint(object):
    '''
        A template, obj pair used to disambiguate which template to
        use when dumping `obj` e.g when present in a multitarget
    '''

    def __init__(self, template, obj):
        self.template = template
        self.obj = obj


class TemplateData(object):
    '''
        Collects the data need to create a object as defined by 'template'
        When created registers targets for sub-objects with the OMXState.

        `template` is the template that data is collected for
        `values` is a list of Target instances for all sub-objects
    '''
    ## TODO
    # add method to verify values are of the proper type ?

    def __init__(self, template, state):
        '''
            `template` a `Template` describing what data should be collected
            `state` a `OmxState` object
        '''

        self.template = template
        add = state.add_target
        self.values = [add(path, name) for (path, name) in template.targets]

    def __repr__(self):
        return '<TemplateData of %r>' % self.template

    def create(self):
        '''
            Creates a new object by calling the factory of the Template with
            the values stored
        '''

        # Build positonal and keyword -arguments
        args = []
        kwargs = {}
        for t in self.values:
            if t.name is None:
                if t.singleton and t.empty:
                    raise Exception(
                        "Missing argument (arg %d to %s): %r" %
                        (len(args) + 1, self.template.match)
                    )
                args.append(t.get())
            else:
                if not t.empty or not t.singleton:
                    kwargs[t.name] = t.get()

        # Create object
        return self.template._factory(*args, **kwargs)

    def dump(self, obj):
        def values(*args, **kwargs):
            args = list(args)
            args.reverse()
            for t in self.values:
                try:
                    if t.name is None:
                        value = args.pop()
                    else:
                        value = kwargs[t.name]
                except (IndexError, KeyError) as e:
                    raise KeyError('No value given for %r' % t)
                t.set(value)
        self.template._serialiser(values, obj)


class TargetDir(object):
    fill = object()

    def __init__(self):
        self.__targets = {}

    def __query(self, path, onaction=None):
        parent = None
        target = None
        current = self.__targets
        for p in path:
            parent = current
            try:
                (current, target) = current[p]
            except KeyError:
                if onaction is self.fill:
                    tmp = ({}, None)
                    current[p] = tmp
                    (current, target) = tmp
                else:
                    raise
        return parent, current, target

    def __dfs(self, val, pre, ctx):
        for i, (child_ctx,t) in ctx.items():
            p = (pre + (i,))
            if t is not None:
                yield val(p, t)
            for x in self.__dfs(val, p, child_ctx):
                yield x

    def get(self, path):
        if not isinstance(path, (tuple, list)):
            raise TypeError("path not a tuple: %r" % path)
        parent, current, target = self.__query(path)
        return target

    def add(self, path, target):
        if not isinstance(path, (tuple, list)):
            raise TypeError("path not a tuple: %r" % path)
        parent, current, old = self.__query(path, self.fill)
        if old is not None:
            raise Exception('Path [%r] already claimed by %r' % (path, old))
        parent[path[-1]] = (current, target)
        return target

    def remove(self, path):
        if not isinstance(path, (tuple, list)):
            raise TypeError("path not a tuple: %r" % path)
        parent, current, target = self.__query(path)
        if len(current) > 0:
            raise Exception('sub-tree not empty')
        del parent[path[-1]]

    def emptytree(self, path):
        if not isinstance(path, (tuple, list)):
            raise TypeError("path not a tuple: %r" % path)
        parent, current, target = self.__query(path)
        current.clear()

    def children(self, path):
        if not isinstance(path, (tuple, list)):
            raise TypeError("path not a tuple: %r" % path)
        parent, current, target = self.__query(path)
        for key, (g, child) in list(current.items()):
            yield (tuple(path) + (key,), child)

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
    def psuedoelement(p):
        t = p[0][-1]
        return t.startswith('@') or t.endswith('()')

    path = ()
    while True:
        try:
            v = dir.get(path)
        except KeyError:
            path = path[:-1]
            continue
        children = dir.children(path)
        try:
            path, v = next(itertools.dropwhile(psuedoelement, children))
        except StopIteration:
            if v is None and path == ():
                return
        yield path, v


class OMXState(object):
    def __init__(self, omx):
        self.omx = omx
        self.path = []
        self.__targets = TargetDir()

    def add_target(self, target, name):
        '''
            Registers elements of `target` relative the current path to be saved
            in new Target named `name`.

            Returns the new `Target` instance.
        '''

        # combine path(s) with current path and detect if the path
        # should be marked as a singleton target
        cls, paths = target
        paths = [tuple((self.path or []) + p) for p in paths]

        # Create handle
        handle = cls(name)

        for path in paths:
            self.__targets.add(path, handle)

        return handle

    def has_target(self):
        return not self.__targets.empty

    def get_target(self, path=None):
        '''
            Get the `Target` instance registered for `path` or the current path
            if None.

            Raises `KeyError` if no `Target` is registered for the path.
        '''

        if path is None:
            path = self.path

        return self.__targets.get(path)

    def remove_target(self, path=None):
        if path is None:
            path = self.path

        return self.__targets.remove(path)

    def prune_targets(self, path):
        ''' Removes all targets registered below `path` '''
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
                yield ap[-1][1:], str(v)

    def get_text(self, path=None):
        for ap, at in self.children(path):
            if ap[-1] == 'text()':
                v = at.pop()
                if at.empty:
                    self.__targets.remove(ap)
                return v
