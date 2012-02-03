import types

def path(pstr):
	if isinstance(pstr, types.StringTypes):
		return pstr.strip(' /').split('/')
	return pstr

def target(tstr):
	if isinstance(tstr, types.StringTypes):
		return [path(p) for p in tstr.split('|')]
	return tstr
