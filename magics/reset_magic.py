from mapyter._MagicPosix import MagicPosix
from mapyter._Notifications import SimpleNotification
from mapyter._PipesHandler import pipes_polling

class ResetMagic(MagicPosix):

    def line_reset(self,line,code,**kwargs):
        """
This magic performs a soft reset of Mapyter. Modules of the magic functions are reloaded. Note that this magic has no effect on the MATLAB session.
        """
        
        msg = "Restarting kernel "
        noti = SimpleNotification(display=self.kernel.Display).showMessage(msg).startProgressWithTimeout(sec=3,small_delay=0.1,extra_counts=5)

        self.kernel.do_shutdown(True)
        
        self.kernel.reload_magics()

        pipes_polling.start_polling()
        
        noti.stopProgress().appendMessage(' done').hideMessageAfter(3)

def register_magics(kernel):
    kernel.register_magics(ResetMagic)
