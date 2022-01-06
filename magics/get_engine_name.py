# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.display import FileLinks
from mapyter._MagicPosix import MagicPosix, option, magic_usage
import os

class GetEngineName(MagicPosix):

    @magic_usage('%%get_engine_name [-h]')
    
    def line_get_engine_name(self,line,code,**kwargs):
        """
Print the name of the shared MATLAB engine.

Examples:

  %get_engine_name
"""
        self.kernel.Display(self.kernel._engine_name)

def register_magics(kernel):
   kernel.register_magics(GetEngineName)
