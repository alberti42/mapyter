import select
import os
import threading
import traceback
import sys
import atexit

STDIN=sys.__stdin__.fileno()
STDOUT=sys.__stdout__.fileno()
STDERR=sys.__stderr__.fileno()

class WrongHashError(Exception): pass
class TimeoutBinaryPipeError(Exception):
    def __init__(self, pipe, timeout):
        self.pipe = pipe
        self.timeout = timeout

    def __str__(self):
        return "Time-out error: communication through {pipe:s} was not properly closed by MATLAB after {timeout:d} seconds from terminating code execution".format(timeout=self.timeout,pipe=self.pipe)

class _PipesHandler():
    """Completely multi-threaded solution. Each pipe gets its own thread and everything is synced at the end."""

    def __init__(self,kernel):
        
        self._kernel = kernel
        self._capture_evnt = threading.Event()
        self._eof_evnt = threading.Event()
        self.packet_size = 4096  # this must be sufficiently big to contain all JSON commands in the binary pipe
        self.pipe_out = self.pipe_in = None # they are overwritten by child classes

        pipes_polling.register(self)
        
    def wait_until_eof(self):
        timeout=1
        if not self._eof_evnt.wait(timeout):
            raise TimeoutBinaryPipeError(timeout=timeout,pipe=self.pipe_type())
                
    def start_capture(self):
        self._capture_evnt.set()
        self._eof_evnt.clear()
        self._eof_evnt_intern = False
        
    def stop_capture(self):
        # to make sure that everything is read out, at the end it pushes
        # onto the buffer an EOF signal and wait for it to be received
        self.signal_eof()
        # wait some time for MATLAB to process the content buffer
        self.wait_until_eof()
        # only at the end stop capturing
        self._capture_evnt.clear()
        
    def show_error(self,e):
        self._kernel.Error(str(e).strip('\n'))
        if __debug__:
            self._kernel.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + "".join(traceback.format_tb(e.__traceback__)))

    def pipe_type(self):
        class_name = type(self).__name__
        if class_name == 'DiaryPipe':
            if self._fileno == STDOUT:
                return 'STDOUT'
            elif self._fileno == STDERR:
                return 'STDERR'
            else:
                return 'PIPE {:d}'.format(self._fileno)
        elif class_name == 'BinaryPipe':
            return 'PIPE BINARY'
        else:
            return 'unknown'
    
    def unregister(self):
        pass

# Polling section
class PipesPolling():
    kernel = None
    _thread = None
    _pipes = {}
    _is_polling = threading.Event()
    _stop_evnt = threading.Event()
    _pipes_obj = []

    def __init__(self):
        atexit.register(self.stop_polling)

    def register(self,obj):
        self._pipes_obj.append(obj)
        
    def poll_loop(self):
        current_pipe = None
        try:
            try:
                # Create a polling object to monitor the different pipes for new data
                poll = select.poll()
                for pipe_out in self._pipes.keys():
                    poll.register(pipe_out, select.POLLIN)
                try:
                    timeout=200
                    self._is_polling.set()
                    while not self._stop_evnt.isSet():
                        # Check if there's data to read
                        poll_results = poll.poll(timeout)
                        for pipe_out,pipe_obj in self._pipes.items():
                            if (pipe_out, select.POLLIN) in poll_results:
                                current_pipe=pipe_out
                                # Timeout specifies the length of time in milliseconds which the system will wait
                                # for events before returning. If timeout is omitted, -1, or None, the call will
                                # block until there is an event for this poll object.
                                
                                packet = os.read(pipe_out, pipe_obj.packet_size)

                                # we always read the buffer to flush it out the
                                # handler decides whether to process it or not
                                try:
                                    pipe_obj.handle_packet(packet)
                                except Exception as e:
                                    self.kernel.Error('An error occurred while communicating with MATLAB through {pipe:s}.'.format(pipe=pipe_obj.pipe_type()))
                                    pipe_obj.show_error(e)
                                current_pipe = None
                finally:
                    for pipe_out in self._pipes.keys():
                        poll.unregister(pipe_out)
            finally:
                for pipe_out,pipe_obj in self._pipes.items():
                    if pipe_obj.pipe_in != pipe_out:
                        os.close(pipe_obj.pipe_in)
                    os.close(pipe_out)
                    pipe_obj.unregister()
                self._is_polling.clear()
                
        except Exception as e:
            if self._pipes and current_pipe:
                extra = ' through {pipe:s}'.format(pipe=self._pipes[current_pipe].pipe_type())
            else:
                extra = ''
            # catch exceptions from the thread and display them in the main thread
            self.kernel.Error("An error occurred in the communication with MATLAB{extra:s}. To resume data streaming you must restart the kernel.".format(extra=extra))
            self.kernel.Error(str(e).strip('\n'))
            if __debug__:
                self.kernel.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + "".join(traceback.format_tb(e.__traceback__)))

    def start_polling(self):
        for pipe_obj in self._pipes_obj:
            pipe_obj.register()
        self._pipes = {pipe_obj.pipe_out:pipe_obj for pipe_obj in self._pipes_obj}
        self._thread=threading.Thread(target=self.poll_loop,daemon=True)
        self._thread.start()

    def stop_polling(self):
        if self._is_polling.isSet():
            self._stop_evnt.set()
            self._thread.join()
            self._stop_evnt.clear()
    
pipes_polling = PipesPolling()
