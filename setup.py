from setuptools import setup, find_packages
import sys, os

version = '0.1.1'

setup(
    name = 'azrcmd',
    version = version,
    description = "Azure Blob Store command line tool to download and upload files.",
    packages = find_packages( exclude = [ 'ez_setup'] ),
    include_package_data = True,
    zip_safe = False,
    author = 'Bence Faludi',
    author_email = 'bence@ozmo.hu',
    license = 'MIT',
    install_requires = [
        'azure-storage',
    ],
    entry_points = {
        'console_scripts': [
            'azrcmd-ls = azrcmd:ls',
            'azrcmd-put = azrcmd:put',
            'azrcmd-rm = azrcmd:rm',
            'azrcmd-get = azrcmd:get'
        ],
    },
    test_suite = 'azrcmd.tests',
    url = 'http://bfaludi.com'
)