# vim: ts=4:sw=4:

from lxml import etree
from .core import OMXState, TemplateData, TemplateHint

class DumpState(OMXState):
    def __init__(self, omx):
        OMXState.__init__(self, omx)

    def dump(self):
        namespace = ''  # FIXME
        for path, target in self.itertargets():
            lpath = list(path)
            repeat = lpath == self.path
            self.path = lpath

            # this could be refactored by merging the two main branches
            if target is None:
                if repeat:
                    yield 'end', path[-1]

                if list(self.children(path)):
                    attributes = dict(self.get_attributes(path))
                    text = self.get_text(path)
                    element = etree.Element(path[-1])
                    element.attrib.update(attributes)
                    element.text = text
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
                if isinstance(target.value, TemplateHint):
                    template = target.value.template
                    value = target.value.obj
                else:
                    template = self.omx.get_template(namespace, path)
                    value = target.value
                data = TemplateData(template, self)
                data.dump(value)
                target.value = data

                # Create element
                element = etree.Element(data.template.match)
                attributes = dict(self.get_attributes(path))
                text = self.get_text(path)
                element.attrib.update(attributes)
                element.text = text
                yield 'start', element
