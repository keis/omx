# vim: ts=4:sw=4:
'''
    Path string grokers

    Placed here in this module because no other place really fit them
'''

import re
from .target import Target, Singleton

try:
    unicode
    strings = (str, unicode)
except NameError:
    strings = str

pathsplit = re.compile('(?:[^/\{]+)|(?:\{[^\}]*\}[^/]*)').findall


def _expandns(path, references):
    if path.startswith('{'):
        return path
    if path.endswith('()'):
        return path
    attrib = path.startswith('@')
    prefix = '@' if attrib else ''
    parts = path[1 if attrib else 0:].split(':', 1)
    ns = ''
    if len(parts) == 2:
        # Leading : forces namespace less element
        if parts[0] != '':
            ns = references[parts[0]]
    elif references is not None and not attrib:
        # Default namespace
        ns = references['']
    if ns:
        return '%s{%s}%s' % (prefix, ns, parts[-1])
    return '%s%s' % (prefix, parts[-1])


def path(pstr, references=None):
    if isinstance(pstr, strings):
        return [_expandns(p, references) for p in pathsplit(pstr.strip(' /'))]
    return pstr


def target(tstr, references=None):
    cls = None

    if isinstance(tstr, tuple) and len(tstr) == 2:
        cls, tstr = tstr

    if isinstance(tstr, strings):
        tstr = tstr.split('|')

    paths = [path(p, references) for p in tstr]

    if cls is None:
        cls = Singleton if singleton(paths) else Target

    return (cls, paths)


def singleton(paths):
    if len(paths) > 1:
        return False
    path, = paths
    if len(path) > 1:
        return False
    return path[-1][0] == '@' or path[-1].endswith('()')
