# vim: noet:ts=4:sw=4:
'''
	Path string grokers

	Placed here in this module because no other place really fit them
'''
import types


def _expandns(path, references):
	if references is None:
		return path
	if path.endswith('()'):
		return path
	parts = path.split(':', 1)
	ns = references[parts[0] if len(parts) == 2 else '']
	if ns:
		return '{%s}%s' % (ns, parts[-1])
	return parts[-1]


def path(pstr, references=None):
	if isinstance(pstr, types.StringTypes):
		return [_expandns(p, references) for p in pstr.strip(' /').split('/')]
	return pstr


def target(tstr, references=None):
	if isinstance(tstr, types.StringTypes):
		return [path(p, references) for p in tstr.split('|')]
	return tstr
