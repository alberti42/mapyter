from ._ThreadsUtils import run_in_stoppable_thread
from time import sleep
import threading
import random
# import IPython.display as disp
           
class SimpleNotification():
    
    def __init__(self,display):
        self._display = display
        self.id = ''.join(random.choices("!#$&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~",k=4))
        self._is_displayed = False
        self._msg = ''

    @property
    def msg(self):
        pass
    
    @msg.setter
    def msg(self,msg):
        self._msg = msg
        self._display(msg,display_id=self.id,update=self._is_displayed)
        self._is_displayed = True

    @msg.getter
    def msg(self):
        return self._msg

    def showMessage(self,msg):
        self.msg = msg
        return self
    
    def appendMessage(self,msg):
        self.msg = self.msg + msg
        return self
        
    def showMessageFor(self,msg,sec):
        self.showMessage(msg)
        self.hideMessageAfter(sec)
        return self
        
    def hideMessage(self):
        self.msg = ''
        return self
    
    def hideMessageAfter(self,sec):
        threading.Timer(sec, self.hideMessage).start()
        return self
    
    def stopProgress(self):
        self._progress.stop_it()
        return self        
        
    def startProgressWithTimeout(self,sec,small_delay=0.1,extra_counts=0,callback=None):
        
        @run_in_stoppable_thread
        def show_progress(is_stopped,obj,cb):
            counts = 0
            extra = 0
            timeout = False
            while extra<=extra_counts and not timeout:
                sleep(small_delay)
                obj.msg = obj.msg + '.'
                counts+=1
                extra+=is_stopped()
                timeout = counts>round(sec/small_delay)
            if cb is not None:
                defaults={'args':{},'kwargs':{}}
                cb = {**defaults,**cb}
                cb['fct'](*cb['args'],**cb['kwargs'])
            else:
                if timeout:
                    obj.msg = obj.msg + ' (time-out error)'
        
        self._progress = show_progress(self,callback).start_it()
        return self


