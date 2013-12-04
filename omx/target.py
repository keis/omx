class Target(object):
    '''
        Holds the data passed to a factory as 'name'

        In general 'data' will be a list of objects created from other templates,
        but may be string when mapped to a attribute or text()

        During load the last item may be an instance of TemplateData.
    '''
    ## TODO
    # check the invariants when setting data

    def __init__(self, name):
        self.name = name
        self.singleton = False
        self._data = []

    def __repr__(self):
        return '<Target %s (%s)>' % (self.name, len(self))

    def __len__(self):
        if self.singleton:
            return 0 if self._data is None else 1
        return len(self._data)

    @property
    def empty(self):
        if self.singleton:
            return self._data is None
        return len(self._data) == 0

    @property
    def value(self):
        if self.singleton:
            if self._data is None:
                raise IndexError("No value set")
            return self._data
        return self._data[-1]

    @value.setter
    def value(self, val):
        if self.singleton:
            self._data = val
        else:
            self._data[-1] = val

    def add(self, value):
        if self.singleton:
            if self._data is not None:
                raise Exception("Value already set for singleton target")
            self._data = value
        else:
            self._data.append(value)

    def pop(self):
        if self.singleton:
            if self._data is None:
                raise IndexError("No value set")
            value = self._data
            self._data = None
        else:
            value = self._data.pop()

        return value

    def get(self):
        return self._data

    def set(self, d):
        if not self.singleton:
            d = list(d)[::-1]
        self._data = d


class Singleton(Target):
    def __init__(self, name):
        Target.__init__(self, name)
        self.singleton = True
        self._data = None
