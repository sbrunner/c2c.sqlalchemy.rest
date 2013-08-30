# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

install_requires = [
    'pyramid',
    'sqlalchemy',
    'geoalchemy',
    'shapely',
]

tests_require = [
    'nosexcover',
    'nose-progressive',
    'ipdbplugin',
    'unittest2',
]

setup(
    name='c2c.sqlalchemy.rest',
    version='0.2.1',
    description='Add a REST interface to simple SQLAlchemy object',
    long_description=README,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Framework :: Buildout :: Recipe',
        'Topic :: System :: Installation/Setup',
    ],
    author='Stéphane Brunner',
    author_email='stephane.brunner@camptocamp.com',
    url='http://github.com/sbrunner/c2c.sqlalchemy.rest',
    license='BSD',
    keywords='sqlalchemy rest',
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    entry_points={
    }
)
