# Copyright (c) Andrea Alberti, 2020

from ipykernel.kernelbase import Kernel

try:
    import matlab.engine as MatlabEngine
    from matlab.engine import MatlabExecutionError, EngineError
except ImportError:
    MatlabEngine = None
    class MatlabExecutionError(Exception): pass
    class EngineError(Exception): pass

from io import StringIO

import json
import os
import sys

from . import __version__

import re

from ._Notifications import SimpleNotification

from ._PipesHandler import STDOUT, STDERR, pipes_polling
from ._BinaryPipe import BinaryPipe
from ._DiaryPipe import DiaryPipe

from ._AnimationUtils import createAnimations

from .parser import Parser

# See https://jupyter-notebook.readthedocs.io/en/stable/comms.html
from ipykernel.comm import CommManager

import traceback

from contextlib import contextmanager

# from ipywidgets.widgets.widget import Widget
Widget = None  # as long as we don't need widgets we can set it to None

import tempfile
import atexit
import shutil
import glob
import importlib
import logging
from logging import config

from jupyter_core.paths import jupyter_config_dir

from IPython.utils.PyColorize import NeutralColors

# FORE_RED = '\x1b[38;2;216;85;83m'
FORE_RED = NeutralColors.colors["header"]
FORE_NORMAL = NeutralColors.colors["normal"]
FORE_CYAN = '\x1b[36m'
FORE_GREEN = '\x1b[32m'
ORANGE = '\x1b[38;2;255;100;0m'
BACK_ROSE = '\x1b[48;2;251;217;217m'
BRIGHT = '\x1b[1m'
RESET_STYLE = '\x1b[0m'

# class ConnectionLostError(Exception): pass
#def _test_link_to_matlab(__ME):
#    if __ME is None or not __ME._check_matlab():
#        raise ConnectionLostError('Error: Connection to MATLAB lost.')

from ._ThreadsUtils import exit_after_with_callback
@exit_after_with_callback(1,None)
def _test_link_to_matlab(__ME):
    ver = __ME.version(nargout=1)
    return ver

def _formatter(data, repr_func):
    reprs = {}
    reprs['text/plain'] = repr_func(data)

    lut = [("_repr_png_", "image/png"),
           ("_repr_jpeg_", "image/jpeg"),
           ("_repr_html_", "text/html"),
           ("_repr_markdown_", "text/markdown"),
           ("_repr_svg_", "image/svg+xml"),
           ("_repr_latex_", "text/latex"),
           ("_repr_json_", "application/json"),
           ("_repr_javascript_", "application/javascript"),
           ("_repr_pdf_", "application/pdf")]

    for (attr, mimetype) in lut:
        obj = getattr(data, attr, None)
        if obj:
            reprs[mimetype] = obj

    format_dict = {}
    metadata_dict = {}
    for (mimetype, value) in reprs.items():
        metadata = None
        try:
            value = value()
        except Exception:
            pass
        if not value:
            continue
        if isinstance(value, tuple):
            metadata = value[1]
            value = value[0]
        if isinstance(value, bytes):
            try:
                value = value.decode('utf_8')
            except Exception:
                # TODO: check the lines below. They were both enabled at the same time
                # which clearly makes no sense. See also note: https://bugs.python.org/issue39351
                # value = base64.encodestring(value)
                # value = value.decode('utf_8')
                pass
        try:
            format_dict[mimetype] = str(value)
        except:
            format_dict[mimetype] = value
        if metadata is not None:
            metadata_dict[mimetype] = metadata
    return (format_dict, metadata_dict)


def _format_message(*objects, **kwargs):
    """
    Format a message like print() does.
    """
    objects = [str(i) for i in objects]
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    return sep.join(objects) + end

class ExceptionWrapper(object):
    def __init__(self, ename, evalue, traceback):
        self.ename = ename
        self.evalue = evalue
        self.traceback = traceback

    def __repr__(self):
        return '{}: {}\n{}'.format(self.ename, self.evalue, self.traceback)

class MatlabKernel2(Kernel):
    # Check https://jupyter-client.readthedocs.io/en/stable/wrapperkernels.html
    app_name = 'mapyter'
    # Information for Kernel info replies. ‘Implementation’ refers to the
    # kernel (e.g. IPython), rather than the language (e.g. Python). The
    # ‘banner’ is displayed to the user in console UIs before the first
    # prompt. All of these values are strings.
    implementation = "Mapyter"
    implementation_version = __version__,
    language = "matlab"
    banner = "Mapyter"
    language_version = __version__,
    # Language information for Kernel info replies, in a dictionary. This
    # should contain the key mimetype with the mimetype of code in the target
    # language (e.g. 'text/x-python'), the name of the language being
    # implemented (e.g. 'python'), and file_extension (e.g. '.py'). It may
    # also contain keys codemirror_mode and pygments_lexer if they need to
    # differ from language.
    language_info = {
        "mimetype": "text/x-matlab",
        "name": "MATLAB",
        "file_extension": ".m",
        "codemirror_mode": "matlab"
    }
    magics_folder = os.path.join(os.path.dirname(__file__),'magics')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_logger()
        
        self._i = None   # it seems never used, probably to be deleted
        self._ii = None
        self._iii = None
        self._ = None
        self.__ = None
        self.___ = None

        self.load_history()    
        
        self.parser = Parser(r'[^\d\W][\w\.]*', r'([^\d\W][\w\.]*)\([^\)\()]*\Z', {'magic':'%', 'shell':'!'})
        
        self.comm_manager = CommManager(parent=self,kernel=self)
        if Widget:
            self.comm_manager.register_target('ipython.widget', Widget.handle_comm_opened)

        self.reload_magics()

        self.tmpdir = tempfile.mkdtemp()
        atexit.register(self.remove_tmpdir)

        here = os.path.dirname(__file__)
        self.intern_m_dir = os.path.join(here,'intern_m')
        self.intern_cpp_dir = os.path.join(here,'intern_cpp')
        self.matlab_m_dir = os.path.join(here,'matlab_m')

        self._import_internal_functions()

        self.__ME = None
        self._load_kernel_json()
        self._show_mat_code = False
                
        self.binary_pipe = BinaryPipe(kernel=self,tmpdir=self.tmpdir)
        self.diary_pipe = DiaryPipe(kernel=self,fileno=STDOUT)
        self.error_pipe = DiaryPipe(kernel=self,fileno=STDERR)

        pipes_polling.kernel = self
        pipes_polling.start_polling()
        
        self._aux = {}  # reset auxiliary blocks
        self.reset_cell_vars()

        import getpass
        self._engine_name = "mapyter_{:s}".format(getpass.getuser())
        
        self.CONNECTION_ERROR = """
Make sure MATLAB is both running and shared. To share a MATLAB session, type the instruction in a MATLAB:
>> matlab.engine.shareEngine('{engine_name:s}');""".format(engine_name=self._engine_name)

    def config_logger(self):

        class ErrorFilter:
            """Allow only LogRecords whose severity levels are below ERROR."""
            def __call__(self, log):
                if log.levelno >= logging.ERROR:
                    return True
                else:
                    return False

        class DebugFilter:
            """Allow only LogRecords whose severity levels are below ERROR."""
            def __call__(self, log):
                if log.levelno < logging.ERROR:
                    return True
                else:
                    return False

        class LoggingFormatter(logging.Formatter):
            """Colored log formatter."""
                    
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)

                self.colors = {
                    'DEBUG': FORE_CYAN,
                    'INFO': FORE_GREEN,
                    'WARNING': ORANGE,
                    'ERROR': FORE_RED,
                    'CRITICAL': FORE_RED + BRIGHT,
                }

            def format(self, record):
                """Format the specified record as text."""

                record.color = self.colors[record.levelname]
                record.reset = RESET_STYLE

                return super().format(record)        

        LOGGING_CONFIG = {
            'version': 1,
            'formatters': {
                'error_formatter': {
                    '()': LoggingFormatter,
                    'format': '{color}{message}{reset}',
                    'style': '{',
                },
                'debug_formatter': {
                    '()': LoggingFormatter,
                    'format': '{color}{message}{reset}',
                    'style': '{',
                },
            },
            'filters': {
                'error_filter': {
                    '()': ErrorFilter,
                },
                'debug_filter': {
                    '()': DebugFilter,
                },
            },
            'handlers': {
                'console_handler': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                    'formatter': 'debug_formatter',
                    'filters': ['debug_filter'],
                },
                'error_handler': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stderr',
                    'formatter': 'error_formatter',
                    'filters': ['error_filter'],
                },
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console_handler', 'error_handler'],
            },
        }

        config.dictConfig(LOGGING_CONFIG)

        self.log = logging.getLogger()

    def remove_tmpdir(self):
        shutil.rmtree(self.tmpdir)    

    def _connect_to_matlab(self):
        success = False
        
        # Checking if Matlab engine is installed
        if MatlabEngine is None:
            err_msg="Error: Matlab engine not installed. Visit https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html for instructions."
            self.Error(err_msg)
            return
        
        msg = "Connecting to MATLAB "
        noti = SimpleNotification(display=self.Display).showMessage(msg).startProgressWithTimeout(sec=10,small_delay=0.1,extra_counts=5)

        try:
            __ME = MatlabEngine.connect_matlab(self._engine_name)
            ver = _test_link_to_matlab(__ME)
            # MATLAB swallows Ctrl-C exceptions when is stuck but then
            # yield None as output, which we can use to rethrow the exception
            if ver is None:
                raise KeyboardInterrupt
        except:
            raise
        else:
            success = True
        finally:
            if not success:
                __ME = None
                msg = " failed"
            else:
                msg = " found MATLAB version {}".format(ver)
            noti.stopProgress().appendMessage(msg).hideMessageAfter(3)
            
        return __ME
        
    def _load_kernel_json(self):
        """Get the kernel json for the kernel.
        """
        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'kernel/kernel.json')) as fid:
            data = json.load(fid)
        data['argv'][0] = sys.executable
        self.kernel_json = data

    @property
    def _ME(self):
        """Property handling connection to MATLAB engine"""
        
        # Since there are several ways to fail, it is safe to keep the state of
        # MATLAB engine local to this function until the function returns with success
        __ME = self.__ME
        self.__ME = None
        
        if __ME:
            try:
                _test_link_to_matlab(__ME)
            except Exception as e:
                # Print out any other error if they occurred, though they should not
                self.Error("Error: Connection to MATLAB lost." + self.CONNECTION_ERROR)
                if __debug__:
                    self.Error(str(e).strip('\n'))
                    self.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + \
                           "".join(traceback.format_tb(e.__traceback__)))
                self.__ME = None # important to set to None to avoid an infinite loop
                __ME = self._ME  # attempts to reconnect
            else:
                self.__ME = __ME
            return __ME
        else:
            try:
                __ME = self._connect_to_matlab()
            except Exception as e:
                self.Error("Error: Cannot connect to MATLAB." + self.CONNECTION_ERROR)
                if __debug__:
                    self.Error(str(e).strip('\n'))
                    self.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + \
                           "".join(traceback.format_tb(e.__traceback__)))
            if __ME == None:
                return None

        self.__ME = __ME

        self._aux = {}  # reset auxiliary blocks

        self._matlab_enter()

        try:
            self.do_execute_direct(self._intern_m['compile_mex'])
        finally:
            self.__ME = None
        if not self._last_exec_state['code']:
            return None
               
        self.__ME = __ME

        return self.__ME

    def _matlab_enter(self):

        ME = self._ME
        if ME:
            ME.warning('off','MATLAB:dispatcher:nameConflict')
            ME.addpath(self.matlab_m_dir,background=False,nargout=0)
            ME.addpath(self.tmpdir,background=False,nargout=0)
            
    def _matlab_exit(self):
        
        ME = self.__ME
        if ME:
            ME.rmpath(self.tmpdir,background=False,nargout=0)
            ME.rmpath(self.matlab_m_dir,background=False,nargout=0)
            ME.warning('on','MATLAB:dispatcher:nameConflict')            
        
    
    def _import_internal_functions(self):

        self._intern_m = {} # dictionary of internal MATLAB functions
        
        join = os.path.join
        
        def _copy(fnc,*args,**kwargs):
            with open(join(self.intern_m_dir,fnc+'.m'),'r') as f:
                code = f.read()
                if args or kwargs:
                    code = code.format(*args,**kwargs)
            with open(join(self.tmpdir,fnc+'.m'),'w') as f:
                f.write(code)
                
        def _import(fnc):
            with open(join(self.intern_m_dir,fnc+'.m'),'r') as f:
                self._intern_m[fnc] = f.read() + '\n'

        _copy('drawnow')
        _copy('figure')
        _copy('clc')
        _copy('parforNotifications')
        _copy('clear',tmpdir=os.path.join(self.tmpdir,'Gc8i96uVM.mat'),args='{:}')
        _copy('openfig')
        _import('precode')
        _import('postcode')
        _import('compile_mex')
        
        self._intern_m['compile_mex'] = self._intern_m['compile_mex'].format(matlab_m=self.matlab_m_dir,intern_cpp=self.intern_cpp_dir)    

    def do_shutdown(self, restart):
        """
        Shut down the app gracefully, saving history.

        https://jupyter-client.readthedocs.io/en/stable/messaging.html#kernel-shutdown
        """
        
        self.save_history()
        
        pipes_polling.stop_polling()

        self._matlab_exit()
        
        # Delete the object MATLAB engine, forcing a new reconnection. All registers
        # like auxiliary functions are reset and the internal MATLAB functions
        # reloaded.
        self.__ME = None
        self._aux = {}  # reset auxiliary blocks
        self.reset_cell_vars()
        
        return {'status': 'ok', 'restart': restart}

    ## Execution functions

    def do_execute(self, code, silent=False, store_history=True, user_expressions=None, allow_stdin=False):
        """Handle code execution.

        https://jupyter-client.readthedocs.io/en/stable/messaging.html#execute
        """

        # Reset count of magics
        self.reset_cell_vars()

        # Set the ability for the kernel to get standard-in:
        self._allow_stdin = allow_stdin
        
        # Create a default response:
        self.kernel_resp = {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

        orig_code = code
        
        if code and store_history:
            self.hist_cache.append(code)

        if not code:
            return self.kernel_resp
    
        self.payload = []
        
        info = self.parse_code(code)
        
        if info['magic']:
            retval = None
            stack = []
            magic = None
            prefixes = ('!','%')
            while code.startswith(prefixes):
                magic = self.call_magic(code)
                if magic is not None:
                    stack.append(magic)
                    code = str(magic.code)
                    # signal to exit, maybe error or no block
                    if not magic.evaluate:
                        break
                else:
                    break
            # Execute code, if any:
            if (magic is None or magic.evaluate) and code != "":
                retval = self.do_execute_direct(orig_code)
            # Post-process magics:
            for magic in reversed(stack):
                retval = magic.post_process(retval)
        else:
            retval = self.do_execute_direct(orig_code)

        self.post_execute(retval, orig_code, silent)

        self.kernel_resp['payload'] = self.payload

        return self.kernel_resp
            
    def do_execute_direct(self, cellcode):

        # Check if MATLAB engine is available
        ME = self._ME
        if not ME:
            return
    
        if self._current_plot_settings is None:
            self._current_plot_settings = self._default_plot_settings # the default values
    
        with self.handling_generic_errors():
            with self.handling_save_dir():
                with self.handling_settings(cellcode=cellcode):
                    if self._show_mat_code:
                        return None
                    with self.handling_progress_bars():
                        with self.handling_movies():
                            with self.handling_matlab_errors():
                                with self.handling_postcode():
                                    # clear makes sure that MATLAB does not use a cache version of Gc8i96uVM_code.m
                                    ME.builtin('clear','Gc8i96uVM_code',nargout=0,background=False)
                                    ME.Gc8i96uVM_code(nargout=0,background=False)

        return None

    def post_execute(self, retval, code, silent):
        """Post-execution actions

        Handle special kernel variables and display response if not silent.
        """
        # Handle in's
        self._iii = self._ii
        self._ii = code
        if (retval is not None):
            # --------------------------------------
            # Handle out's (only when non-null)
            self.___ = self.__
            self.__ = retval
            
            if isinstance(retval, ExceptionWrapper):
                self.kernel_resp['status'] = 'error'
                content = {
                    'traceback':  retval.traceback,
                    'evalue': retval.evalue,
                    'ename': retval.ename,
                }
                self.kernel_resp.update(content)
                if not silent:
                    self.send_response(self.iopub_socket, 'error', content)
            else:
                try:
                    data = _formatter(retval, self.repr)
                except Exception as e:
                    self.Error(e)
                    return
                content = {
                    'execution_count': self.execution_count,
                    'data': data[0],
                    'metadata': data[1],
                }
                if not silent:
                    if Widget and isinstance(retval, Widget):
                        self.Display(retval)
                        return
                    self.send_response(self.iopub_socket, 'execute_result', content)

    def reset_cell_vars(self):
        """book-keeping variables to execute the code in a cell"""
        self._aux_sel = {}  # auxiliary blocks of functions selected in the current cell
        self._current_plot_settings = None
        self._figs = {}
        self._pbars = {}
        self._warnings = {}
        self._warnings_log = {}
        self._last_exec_state = {'code':False,'postcode':False,'movies':False}   

    # Execution context manager functions

    @contextmanager
    def handling_settings(self,cellcode):
    
        cellcode = cellcode+"\n"

        settings = self._current_plot_settings
    
        self.diary_pipe.settings = self._current_plot_settings
        
        if settings['backend']=='native':
            visible_state = 'On'
        elif settings['backend']=='inline':
            if settings['exporter']=='getframe':
                # getframe is much faster when the figure is visible -- we leave it 'off' for now
                visible_state = 'Off'
            else:
                visible_state = 'Off'

        precode=self._intern_m['precode'].format(tmpdir=self.savedir,backend=settings["backend"],\
                                                 fmt=settings["format"],res=settings["resolution"],\
                                                 antialias=settings["antialias"],exporter=settings["exporter"],\
                                                 width=settings["width"],height=settings["height"],fps=settings["fps_eval"],\
                                                 visible=visible_state,movies='true' if settings["movies"] else 'false',\
                                                 export_fig_opts=settings['export_fig'],\
                                                 rescaling=settings['vector_rescaling'],\
                                                 binary_pipe=self.binary_pipe.path)

        postcode=self._intern_m['postcode']

        blks_code=[precode,cellcode]
        blks_meta=[{'offset':0,'lines':precode.count('\n'),'name':'initialization functions'}, \
                   {'offset':0,'lines':cellcode.count('\n'),'name':'cell'}]

        # Load selected auxiliary functions
        for l_md5,aux_name in self._aux_sel.items():
            # Dictionary containing {'code','offset','lines','name'}
            d = self._aux[l_md5]
            # Store in blks_code the value of key 'code' of self._aux[l_md5] 
            blks_code.append(d['code'])
            # Store in blks_meta all keys/values of self._aux[l_md5] except for 'code'
            blks_meta.append({'offset': d['offset'], 'lines':d['lines'], 'name': aux_name})

        with open(os.path.join(self.tmpdir,'Gc8i96uVM_code.m'),'w') as code_m:
            for idx in range(0,len(blks_code)):
                code_m.write(blks_code[idx])

        self._postcode = postcode
        self._blks_code = blks_code
        self._blks_meta = blks_meta

        yield
        pass
    
    @contextmanager
    def handling_save_dir(self):
        # to keep MATLAB response time short when executing the cell code
        # it is important to not write the savedir under tmpdir containing
        # the cell code file Gc8i96uVM_code.m
        with tempfile.TemporaryDirectory() as savedir:
            self.savedir = savedir
            yield
            pass

    @contextmanager
    def handling_progress_bars(self):
        try:
            pass
            yield
        finally:
            for theId,pbar in self._pbars.items():
                self.Display(pbar.close(),display_id=theId,update=True)

    @contextmanager
    def handling_movies(self):
        try:
            yield
        except:
            raise
        else:
            # create animation only if postcode was successful
            if self._last_exec_state['postcode'] and self._figs and self._current_plot_settings['movies']:
                createAnimations(kernel=self,savedir=self.savedir,settings=self._current_plot_settings)
                self._last_exec_state['movies'] = True
            
    @contextmanager
    def handling_matlab_errors(self):
        self.diary_pipe._blks_meta = self._blks_meta
        self.error_pipe._blks_meta = self._blks_meta 
        self.error_pipe.start_capture()
        try:
            yield
        except MatlabExecutionError:
            # We don't need to show the error with stack etc because 
            # matlab errors are handled separately by error_pipe
            pass
        except EngineError:
            self.Error("Error: Connection to MATLAB lost." + self.CONNECTION_ERROR)
        finally:
            pass
            self.error_pipe.stop_capture()

    @contextmanager
    def handling_generic_errors(self):
        try:
            yield
        except Exception as e:
            # Print out any other error if they occurred, though they should not
            self.Error(str(e).strip('\n'))
            if __debug__:
                self.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + \
                       "".join(traceback.format_tb(e.__traceback__)))

    @contextmanager
    def handling_postcode(self):
        self.diary_pipe.start_capture()        
        self.binary_pipe.start_capture()
        
        success = False
        try:
            yield
            self._last_exec_state['code'] = True
            success = True
        finally:
            # Clean up MATLAB workspace. We keep the postcode separated from the code
            # itself because otherwise the user could end up skipping it by typing 'return' at some place in the cell

            with open(os.path.join(self.tmpdir,'Gc8i96uVM_post.m'),'w') as code_m:
                code_m.write(self._postcode)
            
            self._ME.Gc8i96uVM_post(background=False,nargout=0)#,stderr=wrapper_stderr)
            self._last_exec_state['postcode'] = success
            
            # the order is not relevant -- this is because MATLAB writes to the named pipe with blocking mode
            # so that if the receiver is busy, MATLAB has to wait
            self.binary_pipe.stop_capture()
            self.diary_pipe.stop_capture()

    ## Helper functions

    def repr(self, obj):
        return obj
    
    def get_usage(self):
        return "This is the Mapyter."
    
    def get_kernel_help_on(self, info, level=0, none_on_fail=False):
        name = info.get("help_obj", "")
        out = StringIO()
        self._ME.help(name, nargout=0, stdout=out)
        return out.getvalue()

    def load_history(self):
        self.config_dir = os.path.join(jupyter_config_dir(),'mapyter')

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.hist_file = os.path.join(self.config_dir,'history.json')
        try:
            with open(self.hist_file,'r') as f:
                self.hist_cache = json.load(f)
        except:
            self.hist_cache = []
        
    def save_history(self,max_hist_cache=1000):
        with open(self.hist_file, "w") as f:
            json.dump(self.hist_cache[-max_hist_cache:], f)

    ## Comletion functions

    def parse_code(self, code, cursor_start=0, cursor_end=-1):
        """Parse code using our parser."""
        return self.parser.parse_code(code, cursor_start, cursor_end)
        
    def do_complete(self, code, cursor_pos):
        """Handle code completion for the kernel.

        https://jupyter-client.readthedocs.io/en/stable/messaging.html#completion
        """
        info = self.parse_code(code, 0, cursor_pos)
        content = {
            'matches': [],
            'cursor_start': info['start'],
            'cursor_end': info['end'],
            'status': 'ok'
        }

        matches = info['path_matches']
        
        # check that all previous lines are magic
        if info['magic'] and not re.match(".*\n([^%]|%\s).*",info['code'],re.DOTALL):

            # if the last line contains another magic, use that
            line_info = self.parse_code(info['line'])
            if line_info['magic']:
                info = line_info

            if info['magic']['type'] == 'line':
                magics = self.line_magics
            else:
                magics = self.cell_magics
            
            if info['magic']['name'] in magics:
                magic = magics[info['magic']['name']]
                info = info['magic']
                if info['type'] == 'cell' and info['code']:
                    info = self.parse_code(info['code'])
                else:
                    info = self.parse_code(info['args'])

                matches.extend(magic.get_completions(info))

            elif not info['magic']['code'] and not info['magic']['args']:
                matches = []
                for name in magics.keys():
                    if name.startswith(info['magic']['name']):
                        pre = info['magic']['prefix']
                        matches.append(pre + name)
                        info['start'] -= len(pre)
                        info['full_obj'] = pre + info['full_obj']
                        info['obj'] = pre + info['obj']

        else:
            matches.extend(self.get_completions(info))

        if info['full_obj'] and len(info['full_obj']) > len(info['obj']):
            new_list = [m for m in matches if m.startswith(info['full_obj'])]
            if new_list:
                content['cursor_end'] = (content['cursor_end'] +
                                         len(info['full_obj']) -
                                         len(info['obj']))
                matches = new_list

        content["matches"] = sorted(matches)

        return content
    
    def get_completions(self, info):
        """Get completions from kernel based on info dict.
        """

        name = info["obj"]
        compls = self._ME.eval("cell(com.mathworks.jmi.MatlabMCR().mtFindAllTabCompletions('{}', {}, 0))".format(name, len(name)))
        
        # For structs, tables and objects, we need to return `structname.fieldname` instead of just `fieldname`
        if "." in name:
            prefix, _ = name.rsplit(".", 1)
            # if self._ME.eval("isstruct({0}) || istable({0}) || isobject({0})".format(prefix)):  # not necessary
            compls = ["{}.{}".format(prefix, compl) for compl in compls]

        return compls
        
    ## Magic functions

    def call_magic(self, text):
        info = self.parse_code(text)
        
        minfo = info['magic']

        if not minfo:
            return None

        if minfo['type'] == 'cell' and minfo['name'] in self.cell_magics.keys():
            magic = self.cell_magics[minfo['name']]
        elif minfo['type'] == 'line' and minfo['name'] in self.line_magics.keys():
            magic = self.line_magics[minfo['name']]
        else:
            return None

        return magic.call_magic(minfo['type'], minfo['name'], minfo['code'], minfo['args'])

    def register_magics(self, magic_class):
        """Register magics for a given magic_class."""
        magic = magic_class(self)
        line_magics = magic.get_magics('line')
        cell_magics = magic.get_magics('cell')
        for name in line_magics:
            self.line_magics[name] = magic
        for name in cell_magics:
            self.cell_magics[name] = magic

    def reload_magics(self):
        """Reload all of the line and cell magics."""
        self.line_magics = {}
        self.cell_magics = {}
        
        magic_files = []
        paths = [self.magics_folder]
        for magic_dir in paths:
            sys.path.append(magic_dir)
            magic_files.extend(glob.glob(os.path.join(magic_dir, "*.py")))

        for magic in magic_files:
            basename = os.path.basename(magic)
            if basename == "__init__.py":
                continue
            try:
                # load the module dynamically
                spec = importlib.util.spec_from_file_location(os.path.splitext(basename)[0],magic)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.register_magics(self)
            except Exception as e:
                self.log.error("Can't load '{}': error: {}".format(magic, str(e)))
                self.log.error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + \
                       "".join(traceback.format_tb(e.__traceback__)))

    ## Display functions

    def Display(self, *objects, **kwargs):
        """Display one or more objects using rich display.
        See https://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=display#rich-display
        """

        if kwargs.get('update'):
            msg_type = 'update_display_data'
        else:
            msg_type = 'display_data'

        transient = {}
        
        display_id = kwargs.get('display_id',None)

        if display_id:
            transient['display_id'] = display_id

        for item in objects:
            if Widget and isinstance(item, Widget):
                data = {
                    'text/plain': repr(item),
                    'application/vnd.jupyter.widget-view+json': {
                        'version_major': 2,
                        'version_minor': 0,
                        'model_id': item._model_id
                    }
                }
                content = {
                    'data': data,
                    'metadata': {}
                }
                self.send_response(
                    self.iopub_socket,
                    'display_data',
                    content
                )
            else:
                try:
                    data = _formatter(item, self.repr)
                except Exception as e:
                    self.Error(e)
                    return
                content = {
                    'data': data[0],
                    'metadata': data[1],
                    'transient': transient
                }
                self.send_response(
                    self.iopub_socket,
                    msg_type,
                    content
                )

    def Print(self, *objects, **kwargs):
        """Print `objects` to the iopub stream, separated by `sep` and followed by `end`.
        """

        message = _format_message(*objects, **kwargs)
        
        self.Write(message)
        
    def Write(self, message):
        """Write message directly to the iopub stdout with no added end character."""
        
        stream_content = {'name': 'stdout', 'text': message}
        
        self.send_response(self.iopub_socket, 'stream', stream_content)
            
    def Error(self, *objects, **kwargs):
        """Print `objects` to stdout, separated by `sep` and followed by `end`. Objects are cast to strings.
        """
        
        message = _format_message(*objects, **kwargs)
        
        stream_content = {'name': 'stderr', 'text': FORE_RED + message + FORE_NORMAL}

        self.send_response(self.iopub_socket, 'stream', stream_content)

    def clear_output(self, wait=False):
        """Clear the output of the kernel."""
        self.send_response(self.iopub_socket,'clear_output',{'wait': wait})

    def exec_error(self,ename,evalue,traceback):
        """See https://jupyter-client.readthedocs.io/en/latest/messaging.html#execution-errors"""

        # so far functionalities are very limited because these are lacking in the frontend part
        # .../share/jupyter/lab/staging/node_modules/@jupyterlab/logconsole-extension/lib/nboutput.js

        content = {
          'status' : 'error',
           'ename' : ename,   # Exception name, as a string
           'evalue' : evalue,  # Exception value, as a string
           'traceback' : traceback, # traceback frames as strings
        }
        self.send_response(self.iopub_socket,'error',content)
