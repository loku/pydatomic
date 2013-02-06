try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

long_desc=open('README.rst').read()

setup(name="datomic",
      version="0.1.0",
      author="Graham Stratton, Brian Humphrey",
      author_email="gns24@beasts.org, brian.humphrey@loku.com",
      description="Datomic REST API client",
      long_description=long_desc,
      url="https://github.com/loku/pydatomic",
      install_requires=['requests'],
      license='mit',
      py_modules=['datomic', 'edn'],
      classifiers=['Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Topic :: Software Development',
            'Programming Language :: Python',
            'Operating System :: OS Independent']
    )
