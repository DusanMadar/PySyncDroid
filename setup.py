"""PySyncDroid Package handler"""


from setuptools import setup


description = ('A simple way to synchronize an Android device '
               'connected to a Linux PC via MTP over USB')


setup(version='0.0.1',
      name='pysyncdroid',
      url='https://github.com/DusanMadar/PySyncDroid',

      author='Dusan Madar',
      author_email='madar.dusan@gmail.com',

      description=description,
      long_description=description,
      keywords='linux android synchronize usb mtp',

      packages=['pysyncdroid', 'tests'],

      test_suite='tests',
      tests_require=['coverage', 'mock'],

      license='MIT',
      platforms='linux',
      classifiers=['Development Status :: 3 - Alpha',
                   'Programming Language :: Python :: 2.7',
                   'License :: OSI Approved :: MIT License',
                   'Intended Audience :: End Users/Desktop',
                   'Topic :: Desktop Environment :: File Managers'],
      entry_points={'console_scripts': ['pysyncdroid = pysyncdroid.cli:main']}
      )
