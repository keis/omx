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

from hamcrest import assert_that, equal_to
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
from omx import OMX, Namespace, Singleton

case = '''<testcase xmlns="http://test/kv" >
    <object>
        <entry key="foo" value="10"/>
        <entry key="bar" value="7"/>
    </object>
</testcase>'''


def test_load_convert_in_factory():
    ns = Namespace('http://test/kv')

    @ns.template('entry', ('@key', '@value'))
    def entry(key, value):
        return (key, int(value))

    @ns.template('object', ('entry',))
    def obj(entries):
        return dict(entries)

    omx = OMX([ns], [['{http://test/kv}testcase', '{http://test/kv}object']])
    data, = omx.load(StringIO(case))
    assert_that(data, equal_to({
        'foo': 10,
        'bar': 7
    }))


def test_load_dictionary_target():
    ns = Namespace('http://test/kv')

    class AsDict(Singleton):
        def __init__(self, *args):
            Singleton.__init__(self, *args)
            self._data = {}

        def add(self, (key, value)):
            self._data[key] = value

    @ns.template('entry', ('@key', '@value'))
    def entry(key, value):
        return (key, int(value))

    @ns.template('object', ((AsDict, 'entry'),))
    def obj(entries):
        return entries

    omx = OMX([ns], [['{http://test/kv}testcase', '{http://test/kv}object']])
    data, = omx.load(StringIO(case))
    assert_that(data, equal_to({
        'foo': 10,
        'bar': 7
    }))
