from setuptools import setup, find_packages
import os

version = '1.2.dev0'

setup(name='esteele.manager',
      version=version,
      description="Plone release management utilities",
      long_description=open("README.txt").read() + "\n" +
      open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Plone",
          "Programming Language :: Python :: 2.7"
      ],
      keywords='plone release',
      author='Eric Steele',
      author_email='eric@esteele.net',
      url='https://github.com/plone/esteele.manager',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['esteele'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'argh',
          'gitpython>=0.3',
          'configparser',
          'argcomplete',
          'progress',
          'PyGithub',
          'keyring',
          'zest.releaser',
          'docutils',
          'launchpadlib'
      ],
      entry_points={
          'console_scripts': [
              'manage = esteele.manager.manage:manage'],
          'zest.releaser.prereleaser.middle': [
              'show_changelog=esteele.manager.release:show_changelog_entries',
              'check_pypi=esteele.manager.release:check_pypi_access'],
          'zest.releaser.releaser.after': [
              'update_core=esteele.manager.release:update_core']},
      )
