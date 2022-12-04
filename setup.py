from setuptools import find_packages
from setuptools import setup

setup(
    name="gittf",
    version="0.1",
    description="Terraform CI/CD utility",
    packages=['gittf'],
    install_requires=[
        "Click==8.0.1",
        "pyyaml==5.4.1",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
    entry_points={
        "console_scripts": [
            "gittf = gittf.cli:main",
        ]
    },
)
