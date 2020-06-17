"""A setuptools based setup module for GlideinMonitor.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/glideinWMS/glideinmonitor
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='glideinmonitor',
    version='1',
    description='GlideinMonitor Web Server and Indexer',

    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/glideinWMS/glideinmonitor',
    author='GlideinWMS team',
    author_email='glideinwms-support@fnal.gov',
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
    ],
    license="Fermitools Software Legal Information (Modified BSD License)",
    keywords='glideinwms workflow web monitor',

    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'build']),
    include_package_data=True,
    #package_data={'': ['*.sql', '*.html', '*.css', '*.js', 'default_config.json']},

    python_requires='>=3.5',
    setup_requires=['wheel'],
    install_requires=['flask'],

    entry_points={
        'console_scripts': [
            'glideinmonitor-webserver=glideinmonitor.webserver.webserver:main',
            'glideinmonitor-indexer=glideinmonitor.indexer.indexer:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/glideinWMS/glideinmonitor/issues',
        'Source': 'https://github.com/glideinWMS/glideinmonitor',
    },
)
