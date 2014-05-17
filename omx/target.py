class Target(object):
    '''
        Holds the data passed to a factory as 'name'

        In general 'data' will be a list of objects created from other templates,
        but may be string when mapped to a attribute or text()

        During load the last item may be an instance of TemplateData.
    '''

    singleton = False
    scratch = None

    ## TODO
    # check the invariants when setting data

    def __init__(self, name):
        self.name = name
        self._data = []

    def __repr__(self):
        return '<Target(name=%r, size=%r, clean=%r)>' % (self.name, len(self), not self.scratch)

    def __len__(self):
        return len(self._data)

    @property
    def empty(self):
        return len(self) == 0

    def add(self, value):
        self._data.append(value)

    def pop(self):
        return self._data.pop()

    def get(self):
        return self._data

    def set(self, d):
        self._data = list(d)[::-1]


class Singleton(Target):
    singleton = True

    def __init__(self, name):
        Target.__init__(self, name)
        self._data = None

    def __len__(self):
        return 0 if self._data is None else 1

    @property
    def value(self):
        if self._data is None:
            raise IndexError("No value set")
        return self._data

    @value.setter
    def value(self, val):
        self._data = val

    def add(self, value):
        if self._data is not None:
            raise Exception("Value already set for singleton target")
        self._data = value

    def pop(self):
        if self._data is None:
            raise IndexError("No value set")
        value = self._data
        self._data = None
        return value

    def set(self, d):
        self._data = d
