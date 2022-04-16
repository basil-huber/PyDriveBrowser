from setuptools import setup

setup(name='PyDriveBrowser',
      version='0.1.0',
      description='File Browser for Google Drive',
      author='Basil Huber',
      author_email='basil.huber@gmail.com',
      url='https://github.com/basil-huber/PyDriveBrowser',
      project_urls={'Bug Tracker': 'https://github.com/basil-huber/PyDriveBrowser/issues'},
      license='Anti-996',
      packages=['pydrivebrowser'],
      install_requires=['pydrive2', 'pick'],
      zip_safe=False)
