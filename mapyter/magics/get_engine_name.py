# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.display import FileLinks
from mapyter._MagicPosix import MagicPosix, option, magic_usage
from mapyter._Notifications import SimpleNotification

class GetEngineName(MagicPosix):

    @magic_usage('%%get_engine_name [-h]')
    
    def line_get_engine_name(self,line,code,**kwargs):
        """
Print the name of the shared MATLAB engine.

Examples:

  %get_engine_name
"""
        SimpleNotification(display=self.kernel.Display).showMessageFor('The shared MATLAB engine is currently set to: {:s}'.format(self.kernel._engine_name),3)

def register_magics(kernel):
   kernel.register_magics(GetEngineName)
