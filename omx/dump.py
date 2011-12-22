# vim: noet:ts=4:sw=4:

from lxml import etree
from .core import OMXState, TemplateData

class DumpState(OMXState):
	def __init__(self, omx):
		OMXState.__init__(self, omx)

	def dump(self, obj):
		next(self.itertargets())[1].add(obj)

		for path, target in self.itertargets():
			lpath = list(path)
			repeat = lpath == self.path
			self.path = lpath

			# this could be refactored by merging the two main branches
			if target is None:
				if repeat:
					yield 'end', path[-1]

				attributes = dict(self.get_attributes(path))
				if attributes or list(self.children(path)):
					element = etree.Element(path[-1])
					element.attrib.update(attributes)
					yield 'start', element
				else:
					self.remove_target(path)
					self.path.pop()

			else:
				if repeat:
					assert isinstance(target.value, TemplateData)
					yield 'end', path[-1]
					target.pop()

				if target.empty:
					self.remove_target(path)
					self.path.pop()
					continue

				# Set up new template data
				template = self.omx.get_template(path)
				data = TemplateData(template, self)
				data.dump(target.value)
				target.value = data

				# Create element
				element = etree.Element(data.template.match)
				attributes = dict(self.get_attributes(path))
				element.attrib.update(attributes)
				yield 'start', element
