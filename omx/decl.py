# vim: noet:ts=4:sw=4:
'''
	Path string grokers

	Placed here in this module because no other place really fit them
'''

import types
import re

pathsplit = re.compile('(?:[^/\{]+)|(?:\{[^\}]*\}[^/]*)').findall


def _expandns(path, references):
	if path.startswith('{'):
		return path
	if path.endswith('()'):
		return path
	parts = path.split(':', 1)
	ns = ''
	if len(parts) == 2:
		# Leading : forces namespace less element
		if parts[0] != '':
			ns = references[parts[0]]
	elif references is not None:
		# Default namespace
		ns = references['']
	if ns:
		if parts[-1].startswith('@'):
			return '@{%s}%s' % (ns, parts[-1][1:])
		return '{%s}%s' % (ns, parts[-1])
	return parts[-1]


def path(pstr, references=None):
	if isinstance(pstr, types.StringTypes):
		return [_expandns(p, references) for p in pathsplit(pstr.strip(' /'))]
	return pstr


def target(tstr, references=None):
	if isinstance(tstr, types.StringTypes):
		return [path(p, references) for p in tstr.split('|')]
	return tstr
