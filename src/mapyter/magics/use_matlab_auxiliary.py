from mapyter._MagicPosix import MagicPosix, option

from hashlib import md5

class UseMatlabAux(MagicPosix):

    @option("name", action="store", nargs='?', default="", metavar="AUXILIARY_CELL_NAME", help='specify the name of the auxiliary cell to be used')
    def line_use_matlab_auxiliary(self,line,code,**kwargs):
        """
Use the auxiliary cell named AUXILIARY_CELL_NAME when executing the code of this cell.

Example:

To use the auxiliary cell named "auxiliary cell":

  %use_matlab_auxiliary "auxiliary cell"
"""
        # It is forced to check whether a connection to MATLAB exists
        self.kernel._ME
        
        aux_cell_name = kwargs['name']
        aux_cell_name_md5 = md5(aux_cell_name.encode('utf_8')).hexdigest()
        fullname = "standard auxiliary cell" if aux_cell_name == "" else "auxiliary cell named \"{:s}\"".format(aux_cell_name)
            
        if not (aux_cell_name_md5 in self.kernel._aux):
            self.kernel.Error("""Error: Incorrect use of the magic %use_matlab_auxiliary. """ \
                       """The {:s} is not defined yet.""".format(fullname))
            self.evaluate = False
        else:
            self.kernel._aux_sel[aux_cell_name_md5] = fullname
            self.evaluate = True

    @option("name", action="store", nargs='?', default="", metavar="AUXILIARY_CELL_NAME", help='specify the name of the auxiliary cell to be used')
    def cell_use_matlab_auxiliary(self,line,code,**kwargs):
        """
Use the auxiliary cell named AUXILIARY_CELL_NAME when executing the code of this cell.

Example:

To use the auxiliary cell named "auxiliary cell":

  %use_matlab_auxiliary "auxiliary cell"
"""

        self.line_use_matlab_auxiliary(line,code,**kwargs)

def register_magics(kernel):
   kernel.register_magics(UseMatlabAux)
