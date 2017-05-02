from setuptools import setup

setup(name='pyimod',
      version='0.1',
      description='Vitens PI Wrapper',
      url='https://github.com/VitensTC/pyimod/',
      author='Sjoerd Rijpkema',
      author_email='Sjoerd.Rijpkema@vitens.nl',
      packages=['pyimod'],
      install_requires=[
          'pyshp'
      ],
zip_safe=False)