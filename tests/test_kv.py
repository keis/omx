'''A case parsing a dictionary out of kv-list

<testcase xmlns="http://test/kv" >
    <object>
        <entry key="foo" value="10"/>
        <entry key="bar" value="7"/>
    </object>
</testcase>

{
    "foo": 10,
    "bar": 7
}
'''

from hamcrest import assert_that, any_of, equal_to, contains_string
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
from omx import OMX, Namespace, Singleton
from lxml import etree

case = '''<testcase xmlns="http://test/kv" >
    <object>
        <entry key="foo" value="10"/>
        <entry key="bar" value="7"/>
    </object>
</testcase>'''


class AsDict(Singleton):
    def __init__(self, *args):
        Singleton.__init__(self, *args)
        self._data = {}

    def add(self, key_value):
        key, value = key_value
        self._data[key] = value

    def pop(self):
        key = next(iter(self._data))
        return (key, self._data.pop(key))


def test_load_convert_in_factory():
    ns = Namespace('http://test/kv')

    @ns.template('entry', ('@key', '@value'))
    def entry(key, value):
        return (key, int(value))

    @ns.template('object', ('entry',))
    def obj(entries):
        return dict(entries)

    omx = OMX([ns], [['{http://test/kv}testcase', '{http://test/kv}object']])
    data, = omx.load(StringIO(case.encode('utf-8')))
    assert_that(data, equal_to({
        'foo': 10,
        'bar': 7
    }))


def test_load_dictionary_target():
    ns = Namespace('http://test/kv')

    @ns.template('entry', ('@key', '@value'))
    def entry(key, value):
        return (key, int(value))

    @ns.template('object', ((AsDict, 'entry'),))
    def obj(entries):
        return entries

    omx = OMX([ns], [['{http://test/kv}testcase', '{http://test/kv}object']])
    data, = omx.load(StringIO(case.encode('utf-8')))
    assert_that(data, equal_to({
        'foo': 10,
        'bar': 7
    }))


def test_dump_dictionary_target():
    ns = Namespace('')

    @ns.template('entry', ('@key', '@value'))
    def entry(key, value):
        return (key, int(value))

    entry.serialiser(lambda values, obj: values(*obj))

    @ns.template('object', ((AsDict, 'entry'),))
    def obj(entries):
        return entries

    omx = OMX([ns], [['testcase', 'object']])
    data = etree.tostring(omx.dump({'foo': 10, 'bar': 7}))
    if not isinstance(data, str):
        data = data.decode('utf-8')
    assert_that(data, any_of(contains_string('<entry key="bar" value="7"/>'),
                             contains_string('<entry value="7" key="bar"/>')))
    assert_that(data, any_of(contains_string('<entry key="foo" value="10"/>'),
                             contains_string('<entry value="10" key="foo"/>')))
