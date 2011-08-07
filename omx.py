#!/usr/bin/env python2
# vim: noet:ts=4:sw=4:

from omx import Template, OMX

if __name__ == '__main__':  # pragma: no cover
	from StringIO import StringIO
	data = '''<root>
				<persons>
					<person name="foo"/>
					<person name="bar">bla bla</person>
				</persons>
			</root>'''

	roott = Template('root', (), {'persons/person/@name': 'names'},
		lambda names=None: ('root', names),
		lambda obj: ((), {'names': obj[1]}))
	omx = OMX((roott,), 'root')
	v = omx.load(StringIO(data))
	print v

	s = omx.dump(v)
	out = StringIO()
	s.write(out)
	print out.getvalue()
