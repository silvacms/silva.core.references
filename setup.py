from setuptools import setup, find_packages
import os

version = '2.3.2dev'

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
        'dolmen.relations',
        'five.grok',
        'setuptools',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.core.views',
        'zc.relation',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.schema',
        'zope.traversing',
        'zeam.form.base',
        'zeam.form.ztk',
        'zeam.form.silva',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require,
                        'z3c.form': ['z3c.form']},
      entry_points="""
      # -*- Entry points: -*-
      [zeam.form.components]
      references = silva.core.references.widgets.zeamform:register
      """,
      )
