from setuptools import setup

name = "pyjasperclient"
version = "0.1.0"

setup(
    name=name,
    version=version,
    packages=['pyjasperclient',],
    install_requires = ['suds','elementtree'],
)
