from mapyter._MagicPosix import MagicPosix
import os

class PWDMagic(MagicPosix):

    def line_pwd(self,line,code,**kwargs):
        """
Show current directory of session. Note that this is not the same directory as used by MATLAB.
"""
        self.kernel.Print(os.getcwd())


def register_magics(kernel):
    kernel.register_magics(PWDMagic)
