# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.display import FileLinks
from mapyter._MagicPosix import MagicPosix, option, magic_usage
import os

class LSMagic(MagicPosix):

    @magic_usage('%%ls [-h] path')
    @option(
        "-r", "--recursive", action="store_true", default=False, help='recursively descend into subdirectories')
    @option("path", nargs='?', default='.', action="store", help='path to the directory')
    def line_ls(self,line,code,**kwargs):
        """
List files and directories under PATH

Examples:

  %ls .
  
  %ls ~
"""
        path = os.path.abspath(os.path.expanduser(kwargs['path']))
        if not os.path.exists(path):
            self.kernel.Error('Error: no directory found under the path: {path:s}'.format(path=path))
        else:
            self.kernel.Display(FileLinks(path, recursive=kwargs['recursive']))

def register_magics(kernel):
   kernel.register_magics(LSMagic)
