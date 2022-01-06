# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix

class LSMagicMagic(MagicPosix):

    def line_ls_magic(self,line,code,**kwargs):
        """
        %ls_magic - list the current line and cell magics
        
        This line magic will list all of the available cell and line
        magics installed in the system and in your personal magic
        folder.

        Example:
            %lsmagic
        """

        line_magics = self.kernel.line_magics.keys()
        cell_magics = self.kernel.cell_magics.keys()

        out = [
            'Available line magics:',
            '  '.join(sorted([("%" + lm) for lm in line_magics])),
            '',
            'Available cell magics:',
            '  '.join(sorted([("%%" + cm) for cm in cell_magics])),
        ]
        self.kernel.Print('\n'.join(out))

def register_magics(kernel):
    kernel.register_magics(LSMagicMagic)
