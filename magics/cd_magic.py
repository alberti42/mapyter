# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.


from mapyter._MagicPosix import MagicPosix, option
import os


class CDMagic(MagicPosix):

    @option("path", action="store", help='path to the directory')
    def line_cd(self,line,code,**kwargs):
        """
This line magic is used to change the directory of the notebook. Note that this directory
refers to Jupyter Mapyter and is not necessarily the same as that used by MATLAB.

Example:
  
  %cd ..
"""

        path = os.path.expanduser(kwargs['path'])
        try:
            os.chdir(path)
            self.retval = os.path.abspath(path)
        except Exception as e:
            self.kernel.Error(str(e))
            self.retval = None
        

def register_magics(kernel):
    kernel.register_magics(CDMagic)
