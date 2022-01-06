import threading
import _thread as thread

def exit_after_with_callback(s,callback=None):
    """
    Use as decorator to exit process if function takes longer than s seconds
    """ 

    def outer(fn):
        def inner(*args, **kwargs):
            def quit():
                thread.interrupt_main()
                if callback is not None:
                    callback(*args,**kwargs)
            
            timer = threading.Timer(s, quit)
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer
    
def run_after(s):
    """
    Use as decorator to run a function after s seconds
    """ 
    def outer(fn):
        def inner(*args, **kwargs):
            def callback():
                fn(*args, **kwargs)
            
            timer = threading.Timer(s, callback)
            timer.start()
        return inner
    return outer
    

def run_in_stoppable_thread(fun):
    class c(threading.Thread):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.args = args
            self.kwargs = kwargs
            self._stop_evnt = threading.Event()
        
        def start_it(self):
            self.start()
            return self
        
        def stop_it(self):
            self._stop_evnt.set()
            self.join()

        def is_stopped(self):
            return self._stop_evnt.isSet()

        def run(self):
            fun(self.is_stopped,*self.args,**self.kwargs)
    return c
        
