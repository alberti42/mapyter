from mapyter._MagicPosix import MagicPosix

class ShowMATLABcode(MagicPosix):

    def line_show_actual_matlab_code(self,line,code,**kwargs):
        """
Show the MATLAB code running behind the scenes. This magic is useful to debug MATLAB should problems occur. Simply copy and paste the output
of this function into the shared MATLAB session.
        """
        
        self.kernel._show_mat_code = True
        self.evaluate = True

    def post_process(self, retval):
        kernel=self.kernel    
        kernel._show_mat_code = False
        if self.evaluate:
            for idx in range(len(kernel._blks_code)):
                kernel.Print(kernel._blks_code[idx])   

def register_magics(kernel):
    kernel.register_magics(ShowMATLABcode)
