from distutils.core import setup
setup(
  name = 'Mapyter',
  packages = ['mapyter','mapyter.magics'],
  package_dir = {'':'src'},
  version = '1.0',
  description = 'Mapyter - The MATLAB interface for Jupyter',
  author = 'Andrea Alberti',
  author_email = 'a.alberti82@gmail.com',
  url='https://github.com/alberti42/mapyter',
  install_requires=[
        "tqdm",
        "pillow",
    ],
)
