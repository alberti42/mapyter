from mapyter._MagicPosix import MagicPosix, option

from hashlib import md5

from mapyter._Notifications import SimpleNotification

class RMMatlabAux(MagicPosix):
    @option('--all', action='store_true', default=False, help='Unload all auxiliary function cells that were previously loaded')
    @option('name', action='store', nargs='?', default="", metavar="AUXILIARY_CELL_NAME", help='specify the name of the auxiliary cell to be unloaded')
    def line_rm_matlab_auxiliary(self,line,code,**kwargs):

        """
Unload the auxiliary cell named AUXILIARY_CELL_NAME from the memory of Mapyter.

Examples:

To unload the standard auxiliary cell:

  %rm_matlab_auxiliary

To unload an auxiliary cell named "cell name":
  
  %rm_matlab_auxiliary "cell name"

To unload all auxiliary function cells that were previously loaded:

  %rm_matlab_auxiliary --all

Note that the auxiliary cells are not removed from Jupyter notebook. This magic only unloads them from the kernel's memory.
"""
        
        # It is forced to check whether a connection to MATLAB exists
        self.kernel._ME
        
        delete_all = kwargs['all']
        
        if delete_all:
            self.kernel._aux = {}
        else:
            aux_cell_name = kwargs['name']
            aux_cell_name_md5 = md5(aux_cell_name.encode('utf_8')).hexdigest()
            fullname = "standard auxiliary cell" if aux_cell_name == "" else "auxiliary cell named \"{:s}\"".format(aux_cell_name)
            
            if not (aux_cell_name_md5 in self.kernel._aux):
                self.kernel.Error("""Error: Incorrect use of the magic %rm_matlab_auxiliary. """ \
                           """The {:s} is not defined yet.""".format(fullname))
            else:
                self.kernel._aux.pop(aux_cell_name_md5)
                SimpleNotification(display=self.kernel.Display).showMessageFor('{:s} unloaded from kernel space'.format(fullname).capitalize(),3)
        
        self.evaluate = False
        
def register_magics(kernel):
   kernel.register_magics(RMMatlabAux)
