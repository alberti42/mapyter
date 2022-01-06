# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.display import FileLinks
from mapyter._MagicPosix import MagicPosix, option, magic_usage
import os

class SetEngineName(MagicPosix):

    @magic_usage('%%set_engine_name [-h] engine_name')
    @option("engine_name", nargs='?', default='mapyter', action="store", help='name of the shared MATLAB engine')
    def line_set_engine_name(self,line,code,**kwargs):
        """
Change the name of the shared MATLAB engine.

Examples:

  %set_engine_name 'my_own_engine_name'
"""
        self.kernel.Display(kwargs['engine_name'])
        self.kernel._engine_name = kwargs['engine_name']

def register_magics(kernel):
   kernel.register_magics(SetEngineName)
