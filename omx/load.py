# vim: noet:ts=4:sw=4:

from .core import OMXState, TemplateData

class LoadState(OMXState):
	def __init__(self, omx):
		OMXState.__init__(self, omx)
		self.elemtails = []
		self.context = {'ids': {}}

	def push(self, element):
		''' Called when the parser descends into the tree, causing a new element
			to be pushed to the end of the path.

			Initialises a TemplateData instance for the element if needed and fills
			any attribute targets registered for the element

		'''

		self.path.append(element.tag)

		try:
			target = self.get_target()
		except KeyError:
			# An early exit branch should be added to push/pop for the case
			# when a subtree is not mapped to a object
			raise Exception("SKIP not implemented (element without target '%s')"
				% element.tag)

		# Push empty state to text collector
		self.elemtails.append([])

		if target is not None:
			# Create TemplateData instance to collect data of this element
			template = self.omx.get_template(self.path)
			data = TemplateData(template, self)
			target.add(data)
			if 'id' in element.attrib:
				self.context['ids'][element.attrib['id']] = data

		# Fill attribute targets
		for k, v in element.attrib.items():
			try:
				target = self.get_target(self.path + ['@%s' % k])
				target.add(v)
			except KeyError:
				pass

	def pop(self, element):
		''' Called when the parser ascends the tree, causing the last element
			of the path to be popped.

			Fills text() and context() targets
			Replaces target TemplateData with destination object instance.
		'''

		assert self.path[-1] == element.tag

		# Pop text collector state and add the text tail of element
		tails = self.elemtails.pop()
		if len(self.elemtails) > 0:
			self.elemtails[-1].append(element.tail or '')

		# Fill text target: text of current element + tail of all child elements
		try:
			target = self.get_target(self.path + ['text()'])
			text = [element.text or ''] + tails
			target.add(text)
		except KeyError:
			pass

		# Fill context target
		try:
			target = self.get_target(self.path + ['context()'])
			target.add(self.context)
		except KeyError:
			pass

		target = self.get_target()
		self.path.pop()
		if target is None:
			return

		# Create object from TemplateData and clean up
		data = target.value

		assert isinstance(data, TemplateData)
		self.prune_targets(data)

		obj = data.create()

		target.value = obj

		# Save in ID dictionary if id is set
		if 'id' in element.attrib:
			self.context['ids'][element.attrib['id']] = obj
