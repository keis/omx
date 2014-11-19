from contextlib import contextmanager
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.helpers.wrap_matcher import wrap_matcher, is_matchable_type
from hamcrest import assert_that, instance_of
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


class SerializesAs(BaseMatcher):
    def __init__(self, text_matcher):
        self.text_matcher = text_matcher

    def _matches(self, item):
        out = StringIO()
        item.write(out)
        text = out.getvalue().decode('utf-8')
        return self.text_matcher.matches(text)

    def describe_mismatch(self, item, mismatch_description):
        out = StringIO()
        item.write(out)
        text = out.getvalue().decode('utf-8')

        mismatch_description.append_text('was ')
        mismatch_description.append_description_of(item)
        mismatch_description.append_text(' serializing to ')
        mismatch_description.append_description_of(text)

    def describe_to(self, description):
        description.append_text('object serializing to ')
        description.append_description_of(self.text_matcher)


def serializes_as(text):
    return SerializesAs(wrap_matcher(text))


class RaisesContext(object):
    exception = None


@contextmanager
def assert_raises(matcher=None, message=''):
    # Short hand for instance_of matcher
    if is_matchable_type(matcher):
        matcher = instance_of(matcher)
    else:
        matcher = wrap_matcher(matcher)

    context = RaisesContext()
    try:
        yield context
    except Exception as e:
        context.exception = e

    assert_that(context.exception, matcher, message)
