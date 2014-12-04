from hamcrest import assert_that, equal_to, contains_inanyorder
from omx import OMX, Target, Template, template

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


def test_float():
    xmldata = '<foo><data count="5"/><data count="7"/></foo>'
    data = StringIO(xmldata.encode('utf-8'))

    # FIXME: This could be easier
    class Float(Target):
        def add(self, value):
            self._data.append(float(value))

    @template('foo', ((Float, 'data/@count'),))
    def foot(counts):
        return counts

    omx = OMX((foot,), 'foo')
    result = omx.load(data)

    assert_that(result, equal_to([5.0, 7.0]))


def test_dict():
    xmldata = '<foo><data key="foo" value="x"/><data key="bar" value="y"/></foo>'
    data = StringIO(xmldata.encode('utf-8'))

    # FIXME: This could be easier
    class Dict(Target):
        def __init__(self, name):
            self.name = name
            self._data = {}

        def add(self, value):
            key, value = value
            self._data[key] = value

    @template('data', ('@key', '@value'))
    def datat(key, value):
        return key, value

    @template('foo', ((Dict, 'data'),))
    def foot(counts):
        return counts

    omx = OMX((foot, datat), 'foo')
    result = omx.load(data)

    assert_that(result, equal_to({'foo': 'x', 'bar': 'y'}))
