from setuptools import setup

with open('requirements.txt') as file:
   install_deps = [line for line in file]

setup(install_requires=install_deps)
