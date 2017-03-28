from setuptools import setup

name = "pyjasperclient"
version = "0.3.0"

setup(
    name=name,
    version=version,
    description='JasperServer SOAP client for Python',
    packages=['pyjasperclient',],
    install_requires = ['suds-py3'],
    url='https://github.com/agaoglu/pyjasperclient',
    license='Apache',
    author='Erdem Agaoglu',
    author_email='erdem[dot]agaoglu[at]gmail.com'
)
