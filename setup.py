#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# Read the contents of README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version
def get_version():
    version_file = os.path.join(this_directory, 'ipachecker', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    raise RuntimeError('Unable to find version string.')

setup(
    name='ipachecker',
    version=get_version(),
    description='A python tool for checking if an .ipa file is encrypted',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Andres99',
    url='https://github.com/Andres9890/ipachecker',
    project_urls={
        'Bug Reports': 'https://github.com/Andres9890/ipachecker/issues',
        'Source': 'https://github.com/Andres9890/ipachecker',
        'Documentation': 'https://github.com/Andres9890/ipachecker#readme',
    },
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL-3.0 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving',
        'Topic :: Utilities',
    ],
    keywords='ios ipa analysis metadata encryption mobile app',
    python_requires='>=3.8',
    install_requires=[
        'docopt-ng>=0.9.0',
        'rich>=14.1.0',
        'macholib>=1.16.3',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'flake8>=3.8.0',
            'black>=21.0.0',
        ],
        'test': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'ipachecker=ipachecker.__main__:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license='GPL-3.0',
)