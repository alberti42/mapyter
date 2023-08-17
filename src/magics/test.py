from mapyter._MagicPosix import MagicPosix
# import importlib

# from mapyter._BinaryPipe import BinaryPipe
# from mapyter._Notifications import SimpleNotification
# import time
# import inspect
# from ipywidgets import Widget

# import os
# import mapyter._PipesHandler

# from mapyter.magics import plot_magic

class Test(MagicPosix):

    def line_test(self,line,code,**kwargs):


        # f = plot_magic.line_plot

        # print(self.kernel._plot_settings)
        # print()

        # self.kernel.Print('hello')

        # self.kernel.Print(self.kernel._blks_meta)

        # force reloading of the module
                # importlib.reload(module)
               
        # self.kernel.Print(self.kernel.tmpdir)    
        # self.kernel.Print(self.kernel.log)
        # self.kernel._import_internal_functions()

        # print("<"+line+">")
        # print(code)
        # print(kwargs)

        # self.kernel._ME.eval("""global Gc8i96uVM; Gc8i96uVM = struct('builtin',true);""")

        # import logging
        # logger = self.kernel.log
        # logger.setLevel(logging.DEBUG)
        # logging.debug("test")
        # self.kernel.Print('Printing hello in the log')
        
        # import inspect

        # self.kernel.log.warning(inspect.getsource(self.kernel.log.handlers[0].format))
        self.kernel.log.info('hello')
        self.kernel.exec_error('TestError','Test error string',[])

        self.evaluate = False
                
        # self.kernel.Display('hello1',display_id="id1")
        # self.kernel.Display('hello2',display_id="id2")
        # self.kernel.Display('hello3',display_id="id3")
        # self.kernel.Display('hello4',display_id="id1",update=True)
        
        # self.binary_pipe = BinaryPipe(kernel=self,tmpdir=self.kernel.tmpdir).run()

        # print(self.kernel.binary_pipe.path)

        # self.kernel.Print(self.kernel.binary_pipe._pipe_in)

        # self.kernel.Print('binary',self.kernel.binary_pipe._pipe_in)
        # self.kernel.Print('diary',self.kernel.diary_pipe._pipe_in)
        # self.kernel.Print('stderr',self.kernel.error_pipe._pipe_in)

        # self.kernel.diary_pipe.stop_it()
        # self.kernel.error_pipe.stop_it()
        # self.kernel.binary_pipe.stop_it()
        
        # self.kernel.Print('binary',self.kernel.binary_pipe._valid)
        # self.kernel.Print('diary',self.kernel.diary_pipe._valid)
        # self.kernel.Print('stderr',self.kernel.error_pipe._valid)

        # os.write(self.kernel.diary_pipe._pipe_in,"end of it".encode('ascii'))

        # noti = SimpleNotification(display=self.kernel.Display).showMessage('hello world ')
        # time.sleep(1)
        # noti.appendMessage('!!!')
        # noti.hideMessage()

        # _out = noti._out
        # if _out is not None:
        #     _out.data = {}
        #     _out.close()
        #     _out = None

        # if _out is not None:
        #     _out.data = {}
        #     _out.close()
        #     _out = None

        # out = noti._out
        # if out.comm is not None:
        #     Widget.widgets.pop(out.model_id, None)
        #     out.comm.close()
        #     out.comm = None
        #     out._ipython_display_ = None

def register_magics(kernel):
    if True or __debug__:
        kernel.register_magics(Test)
