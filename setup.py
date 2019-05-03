from setuptools import setup

setup(name='enwarlib',
      version='0.0.1',
      description='env var war',
      url='http://github.com/alexhrescale/enwarlib',
      author='alex huang',
      author_email='alexh@rescale.com',
      license='MIT',
      packages=['enwarlib'],
      install_requires=[
          'toolz>=0.8.0',
          'toposort>=1.5',
      ],
)
