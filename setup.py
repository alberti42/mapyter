from distutils.core import setup
setup(
  name = 'Mapyter',
  packages = ['src':'mapyter'],
  version = '1.0',
  description = 'Mapyter - The MATLAB interface for Jupyter',
  author = 'Andrea Alberti',
  author_email = 'a.alberti82@gmail.com',
  install_requires=[
        "tqdm",
        "pillow",
        "jupyter-packaging"
    ],
)
