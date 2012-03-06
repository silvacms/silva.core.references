
from setuptools import setup, find_packages
import os

version = '3.0dev'

tests_require = [
    'Products.Silva [test]',
    ]

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
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.core',],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Products.Formulator',
        'dolmen.relations',
        'five.grok',
        'five.intid',
        'infrae.rest',
        'setuptools',
        'grokcore.chameleon',
        'megrok.pagetemplate',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.core.views',
        'silva.translations',
        'silva.ui',
        'zc.relation',
        'zeam.form.base',
        'zeam.form.silva',
        'zeam.form.ztk',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.publisher',
        'zope.schema',
        'zope.traversing',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      entry_points="""
      [zeam.form.components]
      references = silva.core.references.widgets.zeamform:register
      [zodbupdate]
      renames = silva.core.references:CLASS_CHANGES
      """,
      )
