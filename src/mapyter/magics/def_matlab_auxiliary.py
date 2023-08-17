from mapyter._MagicPosix import MagicPosix, option

from hashlib import md5

from mapyter._Notifications import SimpleNotification

class DefMatlabAux(MagicPosix):

    @option("name", action="store", nargs='?', default="", metavar="AUXILIARY_CELL_NAME", help='define the name of the auxiliary cell when it is provided')
    def cell_def_matlab_auxiliary(self,line,code,**kwargs):
        """
Load the auxiliary cell into the memory of Mapyter and name it AUXILIARY_CELL_NAME. Note that
you if no name is provided, the auxiliary cell will identified as standard auxiliary cell.
        """
        
        # It is forced to check whether a connection to MATLAB exists
        self.kernel._ME
        
        aux_cell_name = kwargs['name']
        aux_cell_name_md5 = md5(aux_cell_name.encode('utf_8')).hexdigest()
        if code[-1] != '\n':
            code+='\n'
        fullname = "standard auxiliary cell" if aux_cell_name == "" else "auxiliary cell named \"{:s}\"".format(aux_cell_name)

        self.kernel._aux[aux_cell_name_md5] = {'code':code,'offset':1,'lines':code.count('\n'),'name':aux_cell_name}
        self.evaluate = False
        SimpleNotification(display=self.kernel.Display).showMessageFor('{:s} loaded into kernel space'.format(fullname).capitalize(),3)

def register_magics(kernel):
   kernel.register_magics(DefMatlabAux)
