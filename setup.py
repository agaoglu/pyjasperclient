from setuptools import setup

name = "pyjasperclient"
version = "0.1.0"

setup(
    name=name,
    version=version,
    packages=['pyjasperclient',],
    install_requires = ['suds','elementtree'],
    url='https://github.com/agaoglu/pyjasperclient',
    author='Erdem Agaoglu',
    author_email='erdem[dot]agaoglu[at]gmail.com'
)
