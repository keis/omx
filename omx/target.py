
class Target(object):
    '''Holds the data passed to a factory as 'name'

    In general 'data' will be a list of objects created from other templates,
    but may be string when mapped to a attribute or text()

    During load the scratch property may hold the TemplateData that will be the next item.
    '''

    # Static field indicating if the target expects a single value
    singleton = False

    # Used to hold value currently being assembled
    scratch = None

    # Pattern being collect to this target
    pattern = None

    def __init__(self, name):
        self.name = name
        self._data = []

    def __repr__(self):
        return '<Target(name=%r, pattern=%r)>' % (self.name, self.pattern)

    @property
    def empty(self):
        '''True if the target is empty

        A empty target indicates to the dumper to stop processing
        '''

        return len(self._data) == 0

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

    @property
    def empty(self):
        return self._data is None

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
