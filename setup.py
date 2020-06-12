#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

# with open('README.rst') as readme_file:
#     readme = readme_file.read()

# with open('HISTORY.rst') as history_file:
#     history = history_file.read()

requirements = ['cbor', ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', 'coverage']

setup(
    author="Bruno Dupuis",
    author_email='lisael@lisael.org',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python Dhall implementation",
    entry_points={
        'console_scripts': [
            'pydhall=pydhall.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    # long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pydhall',
    name='pydhall',
    packages=find_packages(include=['pydhall', 'pydhall.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/lisael/pydhall',
    version='0.1.0',
    zip_safe=False,
)
