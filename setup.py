from setuptools import setup

setup(
    name = 'controlbox connector',
    version = '0.1',

    author = 'Guillaume Libersat',
    description = 'Library for communicating with Controlbox devices',
    license = 'GNU AGPL',

    packages = ['controlbox'],

    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
