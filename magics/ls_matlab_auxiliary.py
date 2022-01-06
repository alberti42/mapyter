from mapyter._MagicPosix import MagicPosix

class LSMatlabAux(MagicPosix):

    def line_ls_matlab_auxiliary(self,line,code,**kwargs):
        """
Print the list of auxiliary function cells that are currently loaded in the memory of Mapyter.
        """

        # It is forced to check whether a connection to MATLAB exists
        self.kernel._ME
        
        if self.kernel._aux:
            txt = ['Currently defined auxiliary cells:\n']
            for idx,v in enumerate(self.kernel._aux.values()):
                theName = "Standard auxiliary cell" if v['name'] == "" else "Auxiliary cell named \"{:s}\"".format(v['name'])
                txt.append("{:d}. {:s}".format(idx+1,theName))
            txt = "\n".join(txt)
        else:
            txt = 'No auxiliary cells defined yet'
            
        self.kernel.Print(txt)
        self.evaluate = False
    

def register_magics(kernel):
   kernel.register_magics(LSMatlabAux)
