#!/usr/bin/env python

from distutils.core import setup

setup(name='ovirt-node-molch',
    version='0.0.1',
    description='oVirt Node COnfiguration TUI',
    author='Fabian Deutsch',
    author_email='fabiand@fedoraproject.org',
    url='http://example.com',
    license="GPLv2+",
    scripts=[
             "bin/ovirt-config-setup"
             ],
    package_dir = {'': 'src'},
    packages=[
        'ovirt',
        'ovirt.node',
        'ovirt.node.ui',
        'ovirt.node.utils',
        'ovirt.node.config',
        'ovirt.node.setup',
        'ovirt.node.installer',
        ],
   data_files=[('extra', ['scm_hash.txt',
                          'Makefile'
                          ]),
#               ('libexec', ['libexec/ovirt-config-setup'
#        '                  ovirt-config-installer']
#                           ])
               ]
)