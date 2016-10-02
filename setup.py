# This file is autogenerated by edgy.project code generator.
# All changes will be overwritten.

from setuptools import setup, find_packages

tolines = lambda c: list(filter(None, map(lambda s: s.strip(), c.split('\n'))))

def read(filename, flt=None):
    with open(filename) as f:
        content = f.read().strip()
        return flt(content) if callable(flt) else content

try:
    version = read('version.txt')
except:
    version = 'dev'

setup(
    name = 'edgy.project',
    description = 'Strongly opinionated python project management.',
    license = 'Apache License, Version 2.0',
    install_requires = ['blessings >=1.6,<1.7',
 'edgy.event >=0.1,<0.2',
 'jinja2 >=2.8,<3.0',
 'six',
 'tornado >=4.4,<4.5'],
    namespace_packages = [u'edgy'],
    version = version,
    long_description = read('README.rst'),
    classifiers = read('classifiers.txt', tolines),
    packages = find_packages(exclude=['ez_setup', 'example', 'test']),
    include_package_data = True,
    extras_require = {'dev': ['coverage >=4.0,<4.2',
         'mock >=2.0,<2.1',
         'pylint >=1.6,<1.7',
         'pytest >=2.9,<2.10',
         'pytest-cov >=2.3,<2.4',
         'sphinx',
         'sphinx_rtd_theme']},
    entry_points = {'console_scripts': ['edgy-project=edgy.project.__main__:main']},
    url = 'https://github.com/python-edgy/project',
    download_url = 'https://github.com/python-edgy/project/tarball/{version}'.format(version=version),
)
