#!/usr/bin/env python2
# vim: ts=4:sw=4:
'''Omx Maps XML

A module for mapping XML into python objects by rules defined by templates

This module uses xpath like paths to designate elements in the tree, but
supports far from all parts of the specification (thus xpath like). In
addition to simple relative paths attributes may be access with @-symbol
and the text of a node with text(), but no other xpath functions is
supported.
'''

## TODO / Wishlist
# Refactor Target singleton checks (method(s) in Target?) Serialisation reusing
# the same templates XML schema from templates ( relax ng ? ) Aliasing or
# Template inheritance Easy singleton targets from template decorator / object
## use [] syntax? like "/foo/bar[0]" ## or something regexp inspired *, +, {3}

__all__ = ('OMX', 'template', 'Template')

from lxml import etree
from .template import template, Template, Namespace
from .target import Target, Singleton

class OMX(object):
    ''' Defines how a XML document is converted into objects '''

    def __init__(self, namespace, root):
        _cls, _paths = decl.target(root)

        self.root = root
        self.ns = {}

        templates = []
        for ns in namespace:
            if isinstance(ns, Template):
                templates.append(ns)
            else:
                self.ns[ns.url] = ns

        # Add any free templates to the unnamed namespace
        if len(templates) > 0:
            if '' not in self.ns:
                self.ns[''] = ns = Namespace('')
            else:
                ns = self.ns['']

            for t in templates:
                ns.add_template(t)

    def get_template(self, namespace, path):
        ''' Get the template used to map path into a object '''
        return self.ns[namespace].get_template(path)

    def load(self, xmldata):
        from .load import LoadState
        ''' Maps 'xmldata' into objects as defined by the templates '''
        state = LoadState(self)
        cls, paths = decl.target(self.root)
        if all(len(x) == 1 for x in paths):
            cls = Singleton
        root_target = state.add_target((cls, paths), 'root', )

        try:
            for event, element in etree.iterparse(xmldata, events=('start', 'end')):
                if event == 'start':
                    state.push(element)
                elif event == 'end':
                    state.pop(element)
                    element.clear()
                else:  # pragma: no cover
                    assert False
        # lxml bug workaround
        except etree.XMLSyntaxError as e:
            if e.text is not None:
                raise e

        return root_target.get()

    def dump(self, obj):
        ''' Maps 'obj' into a xml as defined by the templates '''
        from .dump import DumpState
        state = DumpState(self)
        cls, paths = decl.target(self.root)
        if '/' not in self.root:
            cls = Singleton
        target = state.add_target((cls, paths), 'root')
        target.set(obj)

        stack = []
        for event, element in state.dump():
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
