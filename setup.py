from setuptools import setup

setup(
    name='omx',
    packages=['omx'],
    version='0.1.0',
    author='David Keijser',
    author_email='keijser@gmail.com',
    description='Declarative XML parsing and serialization',
    license='MIT',
    keywords='xml lxml etree declarative',
    extras_require={'tests': ['PyHamcrest']}
)
