from setuptools import setup, find_packages
import os

version = '1.0dev'

setup(name='silva.core.references',
      version=version,
      description="Define a references engine usable by Silva content",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='silva cms references zope',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['silva', 'silva.core',],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'silva.core.rest',
        ],
      )
